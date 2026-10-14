from datetime import date, timedelta, datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .alertas import obtener_alertas_vacaciones
from core.models import Vacacion, Empleado, Proyecto, Macroproyecto, Material, Inventario


def logout_view(request):
    logout(request)
    return redirect("login")


def inicio(request):
    return render(request, "inicio.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/dashboard/")
        else:
            return render(
                request,
                "login.html",
                {"error": "Usuario o contraseña incorrectos. Por favor intenta de nuevo."},
            )

    return render(request, "login.html")


@login_required
def dashboard(request):
    alertas_vacaciones = obtener_alertas_vacaciones()

    ahora = datetime.now()
    meses_es = [
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic",
    ]
    fecha_hoy = f"{ahora.day} {meses_es[ahora.month - 1]}. {ahora.year}"
    hora_hoy = ahora.strftime("%I:%M %p").lower()

    try:
        macroproyectos_count = Macroproyecto.objects.count()
    except Exception:
        macroproyectos_count = 0

    try:
        proyectos_count = Proyecto.objects.count()
    except Exception:
        proyectos_count = 0

    try:
        empleados_count = Empleado.objects.count()
    except Exception:
        empleados_count = 0

    try:
        materiales_count = Material.objects.count()
        inventario_count = Inventario.objects.count()
    except Exception:
        materiales_count = 0
        inventario_count = 0

    try:
        macroproyectos_recientes = list(
            Macroproyecto.objects.prefetch_related("proyectos").order_by("-id")[:5]
        )
    except Exception:
        macroproyectos_recientes = []

    contexto = {
        "alertas_vacaciones": alertas_vacaciones,
        "macroproyectos_count": macroproyectos_count,
        "proyectos_count": proyectos_count,
        "empleados_count": empleados_count,
        "materiales_count": materiales_count,
        "inventario_count": inventario_count,
        "macroproyectos_recientes": macroproyectos_recientes,
        "proyectos_recientes": macroproyectos_recientes,
        "fecha_hoy": fecha_hoy,
        "hora_hoy": hora_hoy,
    }

    return render(request, "dashboard.html", contexto)


