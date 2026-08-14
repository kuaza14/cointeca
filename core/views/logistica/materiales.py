from django.shortcuts import render
from core.models import Material


def materiales_home(request):

    materiales = Material.objects.select_related(
        "inventario"
    ).order_by("item")

    return render(
        request,
        "logistica/materiales/materiales_home.html",
        {
            "materiales": materiales,
        }
    )