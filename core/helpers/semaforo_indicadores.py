import re
from typing import Dict, Any, Optional

def _extraer_numero(texto: str) -> Optional[float]:
    """
    Extrae el primer número (entero o decimal) de una cadena de texto.
    Soporta formato con punto o coma decimal.
    """
    if not texto:
        return None
    # Reemplazar comas entre dígitos por puntos
    limpio = re.sub(r'(\d+),(\d+)', r'\1.\2', str(texto).strip())
    match = re.search(r'[-+]?\d*\.?\d+', limpio)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None

def formatear_decimal(valor: float) -> str:
    """
    Formatea números decimales siguiendo la regla de negocio:
    20 en lugar de 20.0, o 20.5 con separador de punto.
    """
    if valor is None:
        return ""
    val_redondeado = round(valor, 1)
    if val_redondeado.is_integer():
        return str(int(val_redondeado))
    return f"{val_redondeado:.1f}"

def evaluar_semaforo(indicador) -> Dict[str, Any]:
    """
    Evalúa el estado del semáforo para un IndicadorEstrategico
    comparando su meta anual contra el último seguimiento registrado.
    
    Retorna un diccionario con:
    - color: 'verde' | 'amarillo' | 'rojo' | 'gris'
    - texto: 'Cumplido' | 'En Seguimiento' | 'En Riesgo' | 'Sin Mediciones'
    - badge_class: clases Tailwind CSS para insignias
    - icono: emoji representativo
    - porcentaje_cumplimiento: valor numérico o None
    - porcentaje_str: texto formateado como "95%" o "82.5%"
    - ultimo_valor: valor original registrado
    - ultima_fecha: fecha del último seguimiento
    """
    ultimo_seguimiento = indicador.seguimientoindicador_set.order_by('-fecha', '-id').first()
    
    if not ultimo_seguimiento or not ultimo_seguimiento.valor_obtenido:
        return {
            'color': 'gris',
            'texto': 'Sin Mediciones',
            'badge_class': 'bg-slate-100 text-slate-600 border-slate-200',
            'icono': '⚪',
            'porcentaje_cumplimiento': None,
            'porcentaje_str': 'Sin datos',
            'ultimo_valor': None,
            'ultima_fecha': None,
        }

    meta_num = _extraer_numero(indicador.meta_anual)
    valor_num = _extraer_numero(ultimo_seguimiento.valor_obtenido)

    # Si no se pueden inferir números, evaluación por coincidencia de texto
    if meta_num is None or valor_num is None or meta_num == 0:
        meta_limpia = indicador.meta_anual.strip().lower()
        val_limpio = ultimo_seguimiento.valor_obtenido.strip().lower()
        if meta_limpia == val_limpio or 'cumpl' in val_limpio or 'ok' in val_limpio:
            return {
                'color': 'verde',
                'texto': 'Cumplido',
                'badge_class': 'bg-emerald-50 text-emerald-700 border-emerald-200',
                'icono': '🟢',
                'porcentaje_cumplimiento': 100.0,
                'porcentaje_str': '100%',
                'ultimo_valor': ultimo_seguimiento.valor_obtenido,
                'ultima_fecha': ultimo_seguimiento.fecha,
            }
        return {
            'color': 'amarillo',
            'texto': 'En Seguimiento',
            'badge_class': 'bg-amber-50 text-amber-700 border-amber-200',
            'icono': '🟡',
            'porcentaje_cumplimiento': None,
            'porcentaje_str': 'Cualitativo',
            'ultimo_valor': ultimo_seguimiento.valor_obtenido,
            'ultima_fecha': ultimo_seguimiento.fecha,
        }

    # Evaluar si la meta es descendente (menor es mejor, e.g. accidentalidad, reprocesos)
    es_menor_mejor = '<' in indicador.meta_anual or 'menor' in indicador.meta_anual.lower()

    if es_menor_mejor:
        # Menor o igual es Verde
        if valor_num <= meta_num:
            pct = round((meta_num / valor_num) * 100, 1) if valor_num > 0 else 100.0
            color = 'verde'
            texto = 'Cumplido'
            badge_class = 'bg-emerald-50 text-emerald-700 border-emerald-200'
            icono = '🟢'
        elif valor_num <= meta_num * 1.15: # Hasta 15% por encima de la tolerancia
            pct = round((meta_num / valor_num) * 100, 1)
            color = 'amarillo'
            texto = 'En Seguimiento'
            badge_class = 'bg-amber-50 text-amber-700 border-amber-200'
            icono = '🟡'
        else:
            pct = round((meta_num / valor_num) * 100, 1)
            color = 'rojo'
            texto = 'En Riesgo'
            badge_class = 'bg-red-50 text-red-700 border-red-200'
            icono = '🔴'
    else:
        # Mayor o igual es Verde (estándar para ventas, satisfacción, márgenes, etc.)
        pct = round((valor_num / meta_num) * 100, 1)
        if valor_num >= meta_num:
            color = 'verde'
            texto = 'Cumplido'
            badge_class = 'bg-emerald-50 text-emerald-700 border-emerald-200'
            icono = '🟢'
        elif valor_num >= meta_num * 0.85: # A menos del 15% de alcanzar la meta
            color = 'amarillo'
            texto = 'En Seguimiento'
            badge_class = 'bg-amber-50 text-amber-700 border-amber-200'
            icono = '🟡'
        else:
            color = 'rojo'
            texto = 'En Riesgo'
            badge_class = 'bg-red-50 text-red-700 border-red-200'
            icono = '🔴'

    pct_formateado = formatear_decimal(pct) + '%'

    return {
        'color': color,
        'texto': texto,
        'badge_class': badge_class,
        'icono': icono,
        'porcentaje_cumplimiento': pct,
        'porcentaje_str': pct_formateado,
        'ultimo_valor': ultimo_seguimiento.valor_obtenido,
        'ultima_fecha': ultimo_seguimiento.fecha,
    }

def resumen_salud_indicadores(indicadores_queryset=None) -> Dict[str, Any]:
    """
    Genera un consolidado de salud para el conjunto de indicadores estratégicos.
    Utilizado por la Torre de Control de Gerencia.
    """
    if indicadores_queryset is None:
        from core.models import IndicadorEstrategico
        indicadores_queryset = IndicadorEstrategico.objects.all()

    total = 0
    verdes = 0
    amarillos = 0
    rojos = 0
    sin_medicion = 0

    for ind in indicadores_queryset:
        total += 1
        sem = evaluar_semaforo(ind)
        if sem['color'] == 'verde':
            verdes += 1
        elif sem['color'] == 'amarillo':
            amarillos += 1
        elif sem['color'] == 'rojo':
            rojos += 1
        else:
            sin_medicion += 1

    con_datos = verdes + amarillos + rojos
    porcentaje_salud = round((verdes / con_datos * 100), 1) if con_datos > 0 else 0

    return {
        'total': total,
        'verdes': verdes,
        'amarillos': amarillos,
        'rojos': rojos,
        'sin_medicion': sin_medicion,
        'con_datos': con_datos,
        'porcentaje_salud': formatear_decimal(porcentaje_salud),
    }
