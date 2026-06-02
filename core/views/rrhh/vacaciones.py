from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import FileResponse

from docxtpl import DocxTemplate
from datetime import date
import os

from django.conf import settings

from core.models import Empleado

@login_required
def solicitud_vacaciones(request, id):
    empleado = get_object_or_404(Empleado, id=id)

    if request.method == 'POST':
        # generar documento
        pass

    return render(
        request,
        'rrhh/vacaciones/solicitud_vacaciones.html',
        {'empleado': empleado}
    )