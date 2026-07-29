import os

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render


def documentos_rrhh(request):

    return render(
        request,
        "rrhh/documentos/documentos_rrhh.html"
    )


def generar_tratamiento_datos_personales(request):

    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "tratamiento_datos_personales.docx"
    )

    return FileResponse(
        open(ruta, "rb"),
        as_attachment=True,
        filename="tratamiento_datos_personales.docx"
    )

def generar_procedimiento_induccion_capacitacion(request):

    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "procedimiento_induccion_capacitacion.docx"
    )

    return FileResponse(
        open(ruta, "rb"),
        as_attachment=True,
        filename="procedimiento_induccion_capacitacion.docx"
    )

def generar_procedimiento_nomina_prestaciones(request):

    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "procedimiento_nomina_prestaciones.docx"
    )

    return FileResponse(
        open(ruta, "rb"),
        as_attachment=True,
        filename="procedimiento_nomina_prestaciones.docx"
    )

def generar_procedimiento_disciplinario_interno(request):

    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "procedimiento_disciplinario_interno.docx"
    )

    return FileResponse(
        open(ruta, "rb"),
        as_attachment=True,
        filename="procedimiento_disciplinario_interno.docx"
    )

def generar_procedimiento_custodia_historia_clinicas_datos_sensibles(request):

    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "procedimiento_procedimiento_custodia_historia_clinicas_datos_sensibles.docx"
    )

    return FileResponse(
        open(ruta, "rb"),
        as_attachment=True,
        filename="procedimiento_procedimiento_custodia_historia_clinicas_datos_sensibles.docx"
    )

def generar_reglamento_trabajo_cointeca_sas(request):

    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        "reglamento_trabajo_cointeca_sas.docx"
    )

    return FileResponse(
        open(ruta, "rb"),
        as_attachment=True,
        filename="reglamento_trabajo_cointeca_sas.docx"
    )