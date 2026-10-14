import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import render


def _descargar_plantilla_word(nombre_archivo):
    ruta = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        nombre_archivo
    )

    if not os.path.exists(ruta):
        raise Http404(f"La plantilla {nombre_archivo} no existe en el servidor.")

    return FileResponse(
        open(ruta, "rb"),
        as_attachment=True,
        filename=nombre_archivo
    )


@login_required
def documentos_rrhh(request):

    return render(
        request,
        "rrhh/documentos/documentos_rrhh.html"
    )


@login_required
def generar_tratamiento_datos_personales(request):

    return _descargar_plantilla_word("tratamiento_datos_personales.docx")


@login_required
def generar_procedimiento_induccion_capacitacion(request):

    return _descargar_plantilla_word("procedimiento_induccion_capacitacion.docx")


@login_required
def generar_procedimiento_nomina_prestaciones(request):

    return _descargar_plantilla_word("procedimiento_nomina_prestaciones.docx")


@login_required
def generar_procedimiento_disciplinario_interno(request):

    return _descargar_plantilla_word("procedimiento_disciplinario_interno.docx")


@login_required
def generar_procedimiento_custodia_historia_clinicas_datos_sensibles(request):

    return _descargar_plantilla_word(
        "procedimiento_custodia_historia_clinicas_datos_sensibles.docx"
    )


@login_required
def generar_reglamento_trabajo_cointeca_sas(request):

    return _descargar_plantilla_word("reglamento_trabajo_cointeca_sas.docx")
