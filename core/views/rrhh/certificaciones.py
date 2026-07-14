from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from core.utils import formatear_pesos

from datetime import date

from core.models import Empleado
from core.helpers.word import generar_word

@login_required
def certificacion_laboral(request, id):

    empleado = get_object_or_404(
        Empleado,
        id=id
    )

    contexto = {

        "empleado": {

            "nombre_completo": empleado.nombre_completo.upper(),

            "documento": empleado.documento,

            "cargo": empleado.cargo.upper(),

            "salario": formatear_pesos(empleado.salario),

            "fecha_ingreso": empleado.fecha_ingreso.strftime("%d/%m/%Y"),
            "fecha_finalizacion": (
                empleado.fecha_finalizacion.strftime("%d/%m/%Y")
                if empleado.fecha_finalizacion else ""
            ),

            "ciudad_expedicion": empleado.ciudad_expedicion.upper(),

        },

        "fecha_actual": date.today().strftime("%d/%m/%Y")

    }

    return generar_word(

        "certificacion_laboral.docx",

        f"certificacion_{empleado.nombre_completo}.docx",

        contexto

    )