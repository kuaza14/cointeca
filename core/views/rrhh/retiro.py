from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.conf import settings

from docxtpl import DocxTemplate

from datetime import date
import os

from core.models import Empleado


@login_required
def acuerdo_terminacion(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "acuerdo_terminacion.docx"
    )

    doc = DocxTemplate(ruta_plantilla)

    contexto = {

        "empleado": {

            "nombre_completo": empleado.nombre_completo.upper(),

            "documento": empleado.documento,

            "ciudad_expedicion": empleado.ciudad_expedicion.upper(),

            "cargo": empleado.cargo.upper(),

            "fecha_ingreso": empleado.fecha_ingreso.strftime("%d/%m/%Y"),

            "fecha_retiro": (
                empleado.fecha_retiro.strftime("%d/%m/%Y")
                if empleado.fecha_retiro else ""
            ),

            "motivo_retiro": empleado.motivo_retiro,

        },

        "fecha_actual": date.today().strftime("%d/%m/%Y")

    }

    doc.render(contexto)

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"acuerdo_terminacion_{empleado.nombre_completo}.docx"
    )

    doc.save(ruta_salida)

    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"acuerdo_terminacion_{empleado.nombre_completo}.docx"
    )