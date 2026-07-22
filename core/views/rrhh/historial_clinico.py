from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from core.models import Empleado
from core.helpers.word import generar_word, limpiar_nombre_archivo


@login_required
def generar_historia_clinica_laboral(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    hoy = date.today()

    context = {

        # FECHA
        "dia_actual": hoy.day,
        "mes_actual": hoy.strftime("%B"),
        "anio_actual": hoy.year,

        # EMPLEADO
        "nombre_empleado": empleado.nombre_completo,
        "documento_empleado": empleado.documento,
        "ciudad_expedicion": empleado.ciudad_expedicion,

    }

    return generar_word(
        "historial_clinico_laboral.docx",
        limpiar_nombre_archivo(
            f"Consentimiento_Historia_Clinica_{empleado.nombre_completo}.docx"
        ),
        context
    )