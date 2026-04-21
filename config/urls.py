from django.contrib import admin
from django.urls import path
from core.views import inicio, login_view, dashboard, caja_menor, detalle_caja, agregar_movimiento, eliminar_movimiento, editar_movimiento
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('caja-menor/', caja_menor, name='caja_menor'),
    path('caja-menor/<int:id>/', detalle_caja, name='detalle_caja'),
    path('caja-menor/<int:id>/agregar/', agregar_movimiento, name='agregar_movimiento'),
    path('movimiento/<int:id>/eliminar/', eliminar_movimiento, name='eliminar_movimiento'),
    path('movimiento/<int:id>/editar/', editar_movimiento, name='editar_movimiento'),
]

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')