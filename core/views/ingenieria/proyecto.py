from django.shortcuts import render, redirect, get_object_or_404
from core.models import Proyecto, Apoyo


def lista_proyectos(request):

    proyectos = Proyecto.objects.all().order_by("-id")

    return render(
        request,
        "ingenieria/proyecto/lista.html",
        {
            "proyectos": proyectos
        }
    )

def crear_proyecto(request):

    if request.method == "POST":

        Proyecto.objects.create(
            numero_emcali=request.POST.get("numero_emcali"),
            tipo=request.POST.get("tipo")
        )

        return redirect("lista_proyectos")

    return redirect("lista_proyectos")

def detalle_proyecto(request, id):

    proyecto = get_object_or_404(
        Proyecto,
        id=id
    )

    return render(
        request,
        "ingenieria/proyecto/detalle.html",
        {
            "proyecto": proyecto
        }
    )

def lista_apoyos(request, proyecto_id):

    proyecto = get_object_or_404(
        Proyecto,
        id=proyecto_id
    )

    apoyos = Apoyo.objects.filter(
        proyecto=proyecto
    ).order_by("numero_apoyo")

    return render(
        request,
        "ingenieria/apoyos/lista_apoyos.html",
        {
            "proyecto": proyecto,
            "apoyos": apoyos,
        },
    )

def crear_apoyo(request, proyecto_id):

    proyecto = get_object_or_404(
        Proyecto,
        id=proyecto_id
    )

    if request.method == "POST":

        Apoyo.objects.create(
            proyecto=proyecto,
            numero_apoyo=request.POST.get("numero_apoyo"),
            nodo=request.POST.get("nodo"),
        )

    return redirect(
        "lista_apoyos",
        proyecto_id=proyecto.id
    )

def detalle_apoyo(request, apoyo_id):

    apoyo = get_object_or_404(
        Apoyo,
        id=apoyo_id
    )

    return render(
        request,
        "ingenieria/apoyos/detalle_apoyo.html",
        {
            "apoyo": apoyo,
        },
    )