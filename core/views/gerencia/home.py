from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal

from core.models import (
    IndicadorEstrategico,
    ActaJuntaDirectiva,
    ProyectoFacturacion,
    SeguimientoFacturacion,
    CajaMenor,
    MovimientoCajaMenor,
)
from core.helpers.semaforo_indicadores import resumen_salud_indicadores, formatear_decimal


MESES_MAP = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

MESES_NOMBRES = {
    'enero': 'Enero', 'febrero': 'Febrero', 'marzo': 'Marzo', 'abril': 'Abril',
    'mayo': 'Mayo', 'junio': 'Junio', 'julio': 'Julio', 'agosto': 'Agosto',
    'septiembre': 'Septiembre', 'octubre': 'Octubre', 'noviembre': 'Noviembre', 'diciembre': 'Diciembre'
}


@login_required
def gerencia_home(request):
    """
    Vista principal del Módulo de Gerencia & Gobernanza con Torre de Control Ejecutiva.
    Centraliza Actas de Junta Directiva, Indicadores Estratégicos, Facturación y Caja Menor.
    """
    hoy = timezone.now().date()
    mes_actual_cod = MESES_MAP.get(hoy.month, 'enero')
    mes_actual_nombre = MESES_NOMBRES.get(mes_actual_cod, 'Mes Actual')
    anio_actual = hoy.year

    # 1. Metas vs Facturación del Mes
    segs_mes = SeguimientoFacturacion.objects.filter(mes=mes_actual_cod, anio=anio_actual)
    meta_facturacion_mes = sum((s.meta_facturacion for s in segs_mes), Decimal('0'))
    real_facturacion_mes = sum((s.facturacion_real for s in segs_mes), Decimal('0'))
    if meta_facturacion_mes > 0:
        pct_facturacion_num = round(float(real_facturacion_mes / meta_facturacion_mes * 100), 1)
    else:
        pct_facturacion_num = 0.0
    pct_facturacion_str = formatear_decimal(pct_facturacion_num)

    # 2. Salud de Indicadores Estratégicos (Balanced Scorecard)
    salud_kpis = resumen_salud_indicadores()

    # 3. Caja Menor & Gastos Operativos
    cajas = CajaMenor.objects.all()
    caja_total_inicial = sum((c.valor_inicial for c in cajas), Decimal('0'))
    caja_total_gastado = sum((c.total_gastado for c in cajas), Decimal('0'))
    caja_total_restante = sum((c.valor_restante for c in cajas), Decimal('0'))

    # Gastos de caja menor registrados en el mes actual
    movs_mes = MovimientoCajaMenor.objects.filter(fecha__year=anio_actual, fecha__month=hoy.month)
    gasto_caja_mes = sum((m.valor for m in movs_mes), Decimal('0'))

    # 4. Gobernanza: Última Acta de Junta Directiva
    ultima_acta = ActaJuntaDirectiva.objects.order_by('-fecha', '-numero_acta').first()

    # Contadores generales
    total_actas = ActaJuntaDirectiva.objects.count()
    total_indicadores = IndicadorEstrategico.objects.count()
    total_proyectos_facturacion = ProyectoFacturacion.objects.filter(activo=True).count()
    total_seguimientos_facturacion = SeguimientoFacturacion.objects.count()

    contexto = {
        'hoy': hoy,
        'mes_actual_nombre': mes_actual_nombre,
        'anio_actual': anio_actual,
        # Torre de Control
        'meta_facturacion_mes': meta_facturacion_mes,
        'real_facturacion_mes': real_facturacion_mes,
        'pct_facturacion_num': pct_facturacion_num,
        'pct_facturacion_str': pct_facturacion_str,
        'salud_kpis': salud_kpis,
        'caja_total_gastado': caja_total_gastado,
        'caja_total_restante': caja_total_restante,
        'gasto_caja_mes': gasto_caja_mes,
        'ultima_acta': ultima_acta,
        # Contadores de tarjetas
        'total_actas': total_actas,
        'total_indicadores': total_indicadores,
        'total_proyectos_facturacion': total_proyectos_facturacion,
        'total_seguimientos_facturacion': total_seguimientos_facturacion,
    }

    return render(request, 'gerencia/gerencia_home.html', contexto)


@login_required
def plan_estrategico(request):
    """
    Visor oficial del Plan Estratégico Corporativo 2026–2030 (GR-PL-01).
    """
    contexto = {
        'empresa': "COINTECA S.A.S. – INGENIERÍA",
        'horizonte': "2026 – 2030",
        'codigo_documento': "GR-PL-01",
        'mision': (
            "COINTECA S.A.S. cuya razón de ser es contribuir y lograr que nuestro portafolio de servicios "
            "cumpla con la más alta calidad, garantizando una excelente labor en el sector eléctrico mediante "
            "la transferencia del conocimiento, productividad y competitividad. Obteniendo así un bienestar "
            "socioeconómico, cultural y ambiental para nuestros clientes y colaboradores."
        ),
        'vision': (
            "COINTECA S.A.S. quiere ser una reconocida empresa moderna de servicios de ingeniería eléctrica, "
            "con equipos y talento humano calificado que brinden soluciones eficaces, eficientes e idóneas para "
            "las necesidades del sector eléctrico a través de una cultura de mejoramiento continuo e innovación "
            "con aplicaciones tecnológicas de equipos, elementos de protección, control y uso eficiente de los "
            "recursos energéticos."
        ),
        'valores': [
            {
                'titulo': "Excelencia Técnica",
                'icono': "⚡",
                'color': "blue",
                'descripcion': "Rigor en ingeniería eléctrica, cumplimiento estricto de RETIE, NTC 2050 e ISO 50001 en cada obra."
            },
            {
                'titulo': "Ética y Transparencia",
                'icono': "⚖️",
                'color': "indigo",
                'descripcion': "Integridad y claridad en contratos, actas de liquidación bilateral y relaciones con clientes y aliados."
            },
            {
                'titulo': "Responsabilidad",
                'icono': "🛡️",
                'color': "emerald",
                'descripcion': "Compromiso con la seguridad de nuestros colaboradores, bienestar de las comunidades y cuidado del entorno."
            },
            {
                'titulo': "Orientación al Cliente",
                'icono': "🎯",
                'color': "amber",
                'descripcion': "Respuestas ágiles, soluciones idóneas y acompañamiento técnico que maximizan la eficiencia energética."
            },
        ],
        'pilares': [
            {
                'pilar': "Financiero",
                'meta': "Margen por proyecto > 25% y eficacia de recaudo > 90%",
                'foco': "Sostenibilidad, control de costos operativos y optimización de capital de trabajo."
            },
            {
                'pilar': "Comercial & Expansión",
                'meta': "Tasa de cierre solar 15% e incremento del 10% en ticket promedio",
                'foco': "Penetración en proyectos solares fotovoltaicos, redes de distribución y alumbrado público."
            },
            {
                'pilar': "Operativo & Calidad",
                'meta': "100% éxito RETIE y eficiencia en redes > 0.95",
                'foco': "Cero hallazgos en terreno, digitalización de poste a poste y control estricto de materiales."
            },
            {
                'pilar': "Talento & Aprendizaje",
                'meta': "40 horas de capacitación técnica semestral por ingeniero",
                'foco': "Actualización en normativas, seguridad en alturas y tecnologías de vanguardia."
            },
        ]
    }
    return render(request, 'gerencia/plan_estrategico.html', contexto)


@login_required
def descargar_plan_estrategico(request):
    """
    Descarga el documento Word original del Plan Estratégico Corporativo (GR-PL-01).
    """
    import os
    from django.conf import settings
    from django.http import FileResponse, Http404

    ruta = os.path.join(settings.BASE_DIR, 'plantillas_word', 'plan_estrategico_corporativo.docx')
    if not os.path.exists(ruta):
        raise Http404("El archivo del Plan Estratégico no se encuentra disponible.")

    return FileResponse(
        open(ruta, 'rb'),
        as_attachment=True,
        filename="GR-PL-01_Plan_Estrategico_Corporativo_Cointeca_2026_2030.docx"
    )


