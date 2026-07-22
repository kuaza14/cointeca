from django.shortcuts import render
from core.models import Empleado

def dotacion_home(request):

    empleados = Empleado.objects.all().order_by("nombre_completo")

    return render(
        request,
        "logistica/dotacion/index.html",
        {
            "empleados": empleados
        }
    )