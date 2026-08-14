from django.shortcuts import render, redirect, get_object_or_404
from core.models import Proyecto, Apoyo


def ingenieria_inicio(request):

    return render(
        request,
        "ingenieria/ingenieria_inicio.html"
    )

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

    apoyos = Apoyo.objects.filter(
        proyecto=proyecto
    ).order_by("numero_apoyo")

    return render(
        request,
        "ingenieria/proyecto/detalle_proyecto.html",
        {
            "proyecto": proyecto,
            "apoyos": apoyos,
        }
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
        "detalle_proyecto",
        id=proyecto.id
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

def eliminar_apoyo(request, apoyo_id):

    apoyo = get_object_or_404(
        Apoyo,
        id=apoyo_id
    )

    proyecto_id = apoyo.proyecto.id

    if request.method == "POST":
        apoyo.delete()

    return redirect(
        "detalle_proyecto",
        id=proyecto_id
    )