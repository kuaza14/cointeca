from datetime import date, timedelta
from django.db.models import Sum
from core.models import Vacacion, Empleado


def obtener_alertas_vacaciones():
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

    actuales = []
    for vacacion in vacaciones_actuales:
        actuales.append({
            "id": vacacion.empleado.id,
            "empleado": vacacion.empleado.nombre_completo,
            "inicio": vacacion.fecha_inicio,
            "regreso": vacacion.fecha_regreso,
            "dias_restantes": (vacacion.fecha_regreso - hoy).days,
        })

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

    proximas = []
    for vacacion in vacaciones_proximas:
        proximas.append({
            "id": vacacion.empleado.id,
            "empleado": vacacion.empleado.nombre_completo,
            "inicio": vacacion.fecha_inicio,
            "dias_para_salir": (vacacion.fecha_inicio - hoy).days,
        })

    # ==========================
    # 3. PROGRAMAR VACACIONES (Cumplen año en 1 o 2 meses / hasta 60 días)
    # ==========================
    cumplen_anio = []
    pendientes_programar = []

    empleados = Empleado.objects.all().order_by("nombre_completo")

    for empleado in empleados:
        if not empleado.fecha_ingreso:
            continue

        # Próximo aniversario laboral
        try:
            aniversario = empleado.fecha_ingreso.replace(year=hoy.year)
        except ValueError:
            # Caso 29 de febrero en años no bisiestos
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

        dias_tomados = (
            Vacacion.objects.filter(
                empleado=empleado
            ).aggregate(
                total=Sum("dias_tomados")
            )["total"] or 0
        )

        dias_pendientes = max(0, dias_acumulados - dias_tomados)
        proximo_anio_num = anios_trabajados + 1

        # =======================================================
        # ALERTA: Cumple aniversario laboral en 1 o 2 meses (0 a 60 días)
        # =======================================================
        if 0 <= dias_para_aniversario <= 60:
            cumplen_anio.append({
                "id": empleado.id,
                "empleado": empleado.nombre_completo,
                "fecha": aniversario,
                "dias": dias_para_aniversario,
                "anio_num": proximo_anio_num,
                "pendientes": dias_pendientes,
            })

        # =======================================================
        # ALERTA: Ya tiene vacaciones acumuladas sin programar
        # =======================================================
        elif anios_trabajados >= 1 and dias_pendientes > 0:
            pendientes_programar.append({
                "id": empleado.id,
                "empleado": empleado.nombre_completo,
                "anios_trabajados": anios_trabajados,
                "pendientes": dias_pendientes,
            })

    # Ordenar por el que está más próximo a cumplir
    cumplen_anio.sort(key=lambda x: x["dias"])

    return {
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