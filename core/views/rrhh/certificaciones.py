from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import FileResponse

from docxtpl import DocxTemplate
from datetime import date
import os

from django.conf import settings

from core.models import Empleado


@login_required
def certificacion_laboral(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "core",
        "templates",
        "rrhh",
        "contratos",
        "certificacion_laboral.docx"
    )

    doc = DocxTemplate(ruta_plantilla)

    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "cargo": empleado.cargo.upper(),
            "salario": empleado.salario,
            "fecha_ingreso": empleado.fecha_ingreso.strftime("%d/%m/%Y"),
            "ciudad_expedicion": empleado.ciudad_expedicion.upper(),
        },
        "fecha_actual": date.today().strftime("%d/%m/%Y")
    }

    doc.render(contexto)

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"certificacion_{empleado.nombre_completo}.docx"
    )

    doc.save(ruta_salida)

    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"certificacion_{empleado.nombre_completo}.docx"
    )