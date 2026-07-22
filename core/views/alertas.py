from datetime import date, timedelta
from core.models import Vacacion, Empleado
from django.db.models import Sum


def obtener_alertas_vacaciones():

    hoy = date.today()

    # ==========================
    # VACACIONES EN CURSO
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
    pendientes_programar = []

    for vacacion in vacaciones_actuales:

        actuales.append({

                "id": vacacion.empleado.id,

                "empleado": vacacion.empleado.nombre_completo,

                "inicio": vacacion.fecha_inicio,

                "regreso": vacacion.fecha_regreso,

                "dias_restantes": (
                    vacacion.fecha_regreso - hoy
                ).days,

            })

    # ==========================
    # PRÓXIMAS VACACIONES
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

            "dias_para_salir": (
                vacacion.fecha_inicio - hoy
            ).days,
        })

    # ==========================
    # PROGRAMAR VACACIONES
    # ==========================

    cumplen_anio = []

    pendientes_programar = []

    empleados = Empleado.objects.all()

    for empleado in empleados:

        # Próximo aniversario laboral
        aniversario = empleado.fecha_ingreso.replace(year=hoy.year)

        if aniversario < hoy:
            aniversario = aniversario.replace(year=hoy.year + 1)

        dias_para_aniversario = (aniversario - hoy).days

        # Tiempo trabajado
        anios_trabajados = (
            hoy.year - empleado.fecha_ingreso.year
        )

        if (
            (hoy.month, hoy.day)
            <
            (empleado.fecha_ingreso.month, empleado.fecha_ingreso.day)
        ):
            anios_trabajados -= 1

        dias_acumulados = anios_trabajados * 15

        dias_tomados = (
            Vacacion.objects.filter(
                empleado=empleado
            ).aggregate(
                total=Sum("dias_tomados")
            )["total"] or 0
        )

        dias_pendientes = dias_acumulados - dias_tomados

        # ==========================
        # Cumple aniversario en menos de 30 días
        # ==========================

        if 0 <= dias_para_aniversario <= 30:

            cumplen_anio.append({

                "id": empleado.id,

                "empleado": empleado.nombre_completo,

                "fecha": aniversario,

                "dias": dias_para_aniversario,

                "pendientes": dias_pendientes,

            })

        # ==========================
        # Ya tiene vacaciones acumuladas
        # ==========================

        elif anios_trabajados >= 1 and dias_pendientes > 0:

            pendientes_programar.append({

                "empleado": empleado.nombre_completo,

                "pendientes": dias_pendientes,

            })

    return {

        "vacaciones_actuales": actuales,

        "vacaciones_proximas": proximas,

        "cumplen_anio": cumplen_anio,

        "pendientes_programar": pendientes_programar,

    }