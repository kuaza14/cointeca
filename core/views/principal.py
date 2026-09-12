from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .alertas import obtener_alertas_vacaciones
from datetime import date, timedelta, datetime

from core.models import Vacacion, Empleado, Proyecto, ProyectoFacturacion, SeguimientoFacturacion

def logout_view(request):
    logout(request)
    return redirect("login")

# Vista de inicio pública
def inicio(request):
    return render(request, 'inicio.html')

# Vista de login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos. Por favor intenta de nuevo.'})

    return render(request, 'login.html')

# Vista del dashboard principal
@login_required
def dashboard(request):
    alertas_vacaciones = obtener_alertas_vacaciones()

    ahora = datetime.now()
    meses_es = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    fecha_hoy = f"{ahora.day} {meses_es[ahora.month - 1]}. {ahora.year}"
    hora_hoy = ahora.strftime("%I:%M %p").lower()

    # Métricas reales de la Base de Datos
    try:
        proyectos_count = Proyecto.objects.count()
    except Exception:
        proyectos_count = 0

    try:
        empleados_count = Empleado.objects.count()
    except Exception:
        empleados_count = 0

    try:
        from core.models import Material, Inventario
        materiales_count = Material.objects.count()
        inventario_count = Inventario.objects.count()
    except Exception:
        materiales_count = 0
        inventario_count = 0

    try:
        proyectos_recientes = list(Proyecto.objects.order_by('-id')[:5])
    except Exception:
        proyectos_recientes = []

    contexto = {
        'alertas_vacaciones': alertas_vacaciones,
        'proyectos_count': proyectos_count,
        'empleados_count': empleados_count,
        'materiales_count': materiales_count,
        'inventario_count': inventario_count,
        'proyectos_recientes': proyectos_recientes,
        'fecha_hoy': fecha_hoy,
        'hora_hoy': hora_hoy,
    }

    return render(request, 'dashboard.html', contexto)

def obtener_alertas_vacaciones():
    hoy = date.today()
    limite = hoy + timedelta(days=15)

    try:
        vacaciones = Vacacion.objects.select_related('empleado').filter(
            fecha_inicio__gte=hoy,
            fecha_inicio__lte=limite
        ).order_by('fecha_inicio')

        alertas = []
        for vacacion in vacaciones:
            dias = (vacacion.fecha_inicio - hoy).days
            alertas.append({
                "empleado": vacacion.empleado.nombre_completo,
                "fecha": vacacion.fecha_inicio,
                "dias": dias,
            })
        return alertas
    except Exception:
        return []
