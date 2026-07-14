from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from core.helpers.word import generar_word
from datetime import date
from core.models import Empleado


@login_required
def permiso_laboral(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    contexto = {
        "empleado": {
            "nombre_completo": empleado.nombre_completo.upper(),
            "documento": empleado.documento,
            "cargo": empleado.cargo.upper(),
        },
        "fecha_actual": date.today().strftime("%d/%m/%Y"),
    }


    return generar_word(
        "permiso_laboral.docx",
        f"permiso_laboral_{empleado.nombre_completo}.docx",
        contexto
    )
