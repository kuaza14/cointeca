from django.http import FileResponse
from django.conf import settings
from docxtpl import DocxTemplate
import os
import re


def limpiar_nombre_archivo(nombre):
    return re.sub(
        r'[\\/*?:"<>|\t\n]',
        '',
        nombre
    ).strip().replace(
        " ",
        "_"
    )
    
def generar_word(nombre_plantilla, nombre_archivo, contexto):

    ruta_plantilla = os.path.join(
        settings.BASE_DIR,
        "plantillas_word",
        nombre_plantilla
    )

    doc = DocxTemplate(ruta_plantilla)

    doc.render(contexto)

    ruta_salida = os.path.join(
        settings.MEDIA_ROOT,
        nombre_archivo
    )

    doc.save(ruta_salida)

    return FileResponse(
        open(ruta_salida, "rb"),
        as_attachment=True,
        filename=nombre_archivo
    )