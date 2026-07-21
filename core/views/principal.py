from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .alertas import obtener_alertas_vacaciones

def logout_view(request):
    logout(request)
    return redirect("login")

# Vista de inicio 
def inicio(request):
    return render(request, 'inicio.html')

# Vista de login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')  
        else:
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos'})

    return render(request, 'login.html')

# Vista del dashboard
@login_required
def dashboard(request):

    alertas_vacaciones = obtener_alertas_vacaciones()

    return render(
        request,
        'dashboard.html',
        {
            'alertas_vacaciones': alertas_vacaciones
        }
    )

def obtener_alertas_vacaciones():

    hoy = date.today()
    limite = hoy + timedelta(days=15)

    vacaciones = Vacacion.objects.select_related(
        'empleado'
    ).filter(
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
