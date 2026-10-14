from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from core.models import Empleado, Macroproyecto, Material, Inventario


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
    ahora = datetime.now()
    meses_es = [
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic",
    ]
    fecha_hoy = f"{ahora.day} {meses_es[ahora.month - 1]}. {ahora.year}"

    contexto = {
        "macroproyectos_count": Macroproyecto.objects.count(),
        "empleados_count": Empleado.objects.filter(estado="activo").count(),
        "materiales_count": Material.objects.count(),
        "inventario_count": Inventario.objects.filter(cantidad__gt=0).count(),
        "macroproyectos_recientes": list(
            Macroproyecto.objects.prefetch_related("proyectos").order_by("-id")[:5]
        ),
        "fecha_hoy": fecha_hoy,
    }

    return render(request, "dashboard.html", contexto)


