from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from core.models import Empleado

@login_required
def permiso_laboral(request, id):

    empleado = get_object_or_404(Empleado, id=id)

    return render(request, 'rrhh/permisos/index.html', {
        'empleado': empleado
    })