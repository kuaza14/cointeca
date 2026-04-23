from django.contrib import admin
from django.urls import path
from core.views import inicio, login_view, dashboard, caja_menor, detalle_caja, agregar_movimiento, eliminar_movimiento, editar_movimiento, actas, crear_acta, detalle_acta, editar_acta, eliminar_acta, indicadores, crear_indicador, detalle_indicador, agregar_seguimiento, eliminar_indicador, editar_indicador, editar_seguimiento, eliminar_seguimiento   
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
    path('actas/', actas, name='actas'),
    path('actas/crear/', crear_acta, name='crear_acta'),
    path('actas/<int:id>/', detalle_acta, name='detalle_acta'),
    path('actas/<int:id>/editar/', editar_acta, name='editar_acta'),
    path('actas/<int:id>/eliminar/', eliminar_acta, name='eliminar_acta'),
    path('indicadores/', indicadores, name='indicadores'),
    path('indicadores/crear/', crear_indicador, name='crear_indicador'),
    path('indicadores/<int:id>/', detalle_indicador, name='detalle_indicador'),
    path('indicadores/<int:id>/agregar-seguimiento/', agregar_seguimiento, name='agregar_seguimiento'),
    path('indicadores/<int:id>/eliminar/', eliminar_indicador, name='eliminar_indicador'),
    path('indicadores/<int:id>/editar/', editar_indicador, name='editar_indicador'),
    path('seguimiento/<int:id>/editar/', editar_seguimiento, name='editar_seguimiento'),
    path('seguimiento/<int:id>/eliminar/', eliminar_seguimiento, name='eliminar_seguimiento'),
    path('indicadores/<int:id>/seguimiento/', agregar_seguimiento, name='agregar_seguimiento'),
]
