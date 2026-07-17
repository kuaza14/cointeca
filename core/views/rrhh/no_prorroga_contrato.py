from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from core.models import Empleado
from core.helpers.word import generar_word, limpiar_nombre_archivo


@login_required
def generar_no_prorroga_contrato(request, id):

    empleado = get_object_or_404(Empleado, id=id)
    hoy = date.today()

    context = {
        # FECHA ACTUAL
        'dia_actual': hoy.day,
        'mes_actual': hoy.strftime('%B'),
        'anio_actual': hoy.year,

        # EMPLEADO
        'nombre_empleado': empleado.nombre_completo,
        'cargo_empleado': empleado.cargo,

        # FINALIZACIÓN DEL CONTRATO
        'fecha_finalizacion': (
            empleado.fecha_finalizacion.strftime('%d/%m/%Y')
            if empleado.fecha_finalizacion
            else ''
        ),

        # FIRMANTE
        'nombre_firmante': '',
        'cargo_firmante': '',
    }

    return generar_word(
        'no_prorroga_contrato.docx',
        limpiar_nombre_archivo(
            f'No_Prorroga_Contrato_{empleado.nombre_completo}.docx'
        ),
        context
    )