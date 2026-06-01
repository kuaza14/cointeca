from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.conf import settings

from docxtpl import DocxTemplate

import os

from core.models import (
    Empleado
)

@login_required
def generar_contrato(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "core",
        "templates",
        "rrhh",
        "contratos",
        "test.docx"
    )

    # ABRIR PLANTILLA
    doc = DocxTemplate(ruta_plantilla)

    # VARIABLES
    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "direccion": empleado.direccion.upper(),
            "telefono": empleado.telefono,
            "cargo": empleado.cargo.upper(),
            "salario": empleado.salario,
            "fecha_ingreso": empleado.fecha_ingreso.strftime("%d/%m/%Y"),
            "fecha_finalizacion": empleado.fecha_finalizacion.strftime("%d/%m/%Y") if empleado.fecha_finalizacion else None,
            "tipo_contrato": empleado.tipo_contrato.upper(),
            "jornada": empleado.jornada.upper(),
            "ciudad_expedicion": empleado.ciudad_expedicion.upper(),
            "nacionalidad": empleado.nacionalidad.upper(),
            "ciudad_residencia": empleado.ciudad_residencia.upper(),
            "correo": empleado.correo.upper(),

        }
    }

    # REEMPLAZAR VARIABLES
    doc.render(contexto)

    # GUARDAR NUEVO WORD
    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        f"contrato_{empleado.nombre_completo}.docx"
    )

    doc.save(ruta_salida)

    # DESCARGAR
    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=f"contrato_{empleado.nombre_completo}.docx"
    )