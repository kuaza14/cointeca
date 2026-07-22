from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from core.models import Empleado
from core.helpers.word import generar_word, limpiar_nombre_archivo

@login_required
def generar_acuerdo_responsabilidad(request, id):

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
        "fecha_actual": hoy.strftime("%d/%m/%Y"),

    }

    return generar_word(
        "acuerdo_autorizacion_descuento.docx",
        limpiar_nombre_archivo(
            f"Acuerdo_responsabilidad_{empleado.nombre_completo}.docx"
        ),
        context
    )