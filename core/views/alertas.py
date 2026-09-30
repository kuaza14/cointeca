import time
from datetime import date, timedelta
from django.db.models import Sum
from core.models import Vacacion, Empleado

# Cache en memoria para evitar ejecutar múltiples consultas pesadas en cada navegación
_ALERTAS_CACHE = {
    'timestamp': 0,
    'data': None,
}


def invalidar_cache_alertas():
    """Limpia el caché de alertas para forzar recálculo inmediato."""
    _ALERTAS_CACHE['timestamp'] = 0
    _ALERTAS_CACHE['data'] = None


def obtener_alertas_vacaciones():
    ahora_ts = time.time()
    # Retornar caché en memoria si tiene menos de 5 minutos (300 segundos)
    if _ALERTAS_CACHE['data'] is not None and (ahora_ts - _ALERTAS_CACHE['timestamp']) < 300:
        return _ALERTAS_CACHE['data']

    hoy = date.today()

    # ==========================
    # 1. VACACIONES EN CURSO (Empleados actualmente en descanso)
    # ==========================
    vacaciones_actuales = (
        Vacacion.objects.select_related("empleado")
        .filter(
            fecha_inicio__lte=hoy,
            fecha_regreso__gt=hoy
        )
        .order_by("fecha_regreso")
    )

    actuales = [
        {
            "id": v.empleado.id,
            "empleado": v.empleado.nombre_completo,
            "inicio": v.fecha_inicio,
            "regreso": v.fecha_regreso,
            "dias_restantes": (v.fecha_regreso - hoy).days,
        }
        for v in vacaciones_actuales
    ]

    # ==========================
    # 2. PRÓXIMAS VACACIONES (Salen en los próximos 15 días)
    # ==========================
    vacaciones_proximas = (
        Vacacion.objects.select_related("empleado")
        .filter(
            fecha_inicio__gt=hoy,
            fecha_inicio__lte=hoy + timedelta(days=15)
        )
        .order_by("fecha_inicio")
    )

    proximas = [
        {
            "id": v.empleado.id,
            "empleado": v.empleado.nombre_completo,
            "inicio": v.fecha_inicio,
            "dias_para_salir": (v.fecha_inicio - hoy).days,
        }
        for v in vacaciones_proximas
    ]

    # ==========================
    # 3. PROGRAMAR VACACIONES (Optimizado: 1 sola consulta SQL agrupada)
    # ==========================
    cumplen_anio = []
    pendientes_programar = []

    # Obtenemos los días tomados de TODOS los empleados en una única consulta GROUP BY
    dias_tomados_map = dict(
        Vacacion.objects.values_list("empleado_id")
        .annotate(total=Sum("dias_tomados"))
    )

    empleados = (
        Empleado.objects.filter(fecha_ingreso__isnull=False)
        .only("id", "nombre_completo", "fecha_ingreso")
        .order_by("nombre_completo")
    )

    for empleado in empleados:
        if not empleado.fecha_ingreso:
            continue

        # Próximo aniversario laboral
        try:
            aniversario = empleado.fecha_ingreso.replace(year=hoy.year)
        except ValueError:
            aniversario = empleado.fecha_ingreso.replace(year=hoy.year, day=28)

        if aniversario < hoy:
            try:
                aniversario = empleado.fecha_ingreso.replace(year=hoy.year + 1)
            except ValueError:
                aniversario = empleado.fecha_ingreso.replace(year=hoy.year + 1, day=28)

        dias_para_aniversario = (aniversario - hoy).days

        # Antigüedad en años trabajados cumplidos
        anios_trabajados = hoy.year - empleado.fecha_ingreso.year
        if (hoy.month, hoy.day) < (empleado.fecha_ingreso.month, empleado.fecha_ingreso.day):
            anios_trabajados -= 1

        dias_acumulados = max(0, anios_trabajados * 15)
        dias_tomados = dias_tomados_map.get(empleado.id) or 0
        dias_pendientes = max(0, dias_acumulados - dias_tomados)
        proximo_anio_num = anios_trabajados + 1

        if 0 <= dias_para_aniversario <= 60:
            cumplen_anio.append({
                "id": empleado.id,
                "empleado": empleado.nombre_completo,
                "fecha": aniversario,
                "dias": dias_para_aniversario,
                "anio_num": proximo_anio_num,
                "pendientes": dias_pendientes,
            })
        elif anios_trabajados >= 1 and dias_pendientes > 0:
            pendientes_programar.append({
                "id": empleado.id,
                "empleado": empleado.nombre_completo,
                "anios_trabajados": anios_trabajados,
                "pendientes": dias_pendientes,
            })

    cumplen_anio.sort(key=lambda x: x["dias"])

    resultado = {
        "vacaciones_actuales": actuales,
        "vacaciones_proximas": proximas,
        "cumplen_anio": cumplen_anio,
        "pendientes_programar": pendientes_programar,
        "total_alertas": (
            len(actuales)
            + len(proximas)
            + len(cumplen_anio)
            + len(pendientes_programar)
        ),
    }

    _ALERTAS_CACHE['timestamp'] = ahora_ts
    _ALERTAS_CACHE['data'] = resultado
    return resultado