from django.shortcuts import render
from core.models import Proyecto


def lista_proyectos(request):

    proyectos = Proyecto.objects.all().order_by("-id")

    return render(
        request,
        "ingenieria/proyecto/lista.html",
        {
            "proyectos": proyectos
        }
    )