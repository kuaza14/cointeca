from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# =========================
# 🔵 VIEWS PRINCIPALES
# =========================
from core.views import (
    inicio,
    login_view,
    dashboard,
    caja_menor,
    detalle_caja,
    agregar_movimiento,
    eliminar_movimiento,
    editar_movimiento,
    actas,
    crear_acta,
    detalle_acta,
    editar_acta,
    eliminar_acta,
    indicadores,
    crear_indicador,
    detalle_indicador,
    agregar_seguimiento,
    eliminar_indicador,
    editar_indicador,
    editar_seguimiento,
    eliminar_seguimiento,
    facturacion,
    crear_proyecto,
    registrar_facturacion,
    eliminar_facturacion,
    editar_facturacion,
)

# 🟢 RRHH - EMPLEADOS
# =========================
from core.views.rrhh.empleados import (
    rrhh_home,
    empleados,
    crear_empleado,
    detalle_empleado,
    eliminar_empleado,
    agregar_dotacion,
    subir_documento,
    eliminar_documento,
)

# 🟡 RRHH - CERTIFICACIONES
# =========================
from core.views.rrhh.certificaciones import certificacion_laboral

# 🟣 RRHH - PERMISOS (SI EXISTE ARCHIVO)
# =========================
from core.views.rrhh.permisos import permiso_laboral

from core.views.rrhh.equipos import asignar_equipo, eliminar_equipo, editar_equipo, acta_entrega_equipos, inventario_equipos, crear_equipo_inventario, editar_equipo_inventario, eliminar_equipo_inventario

from core.views.rrhh.contratos import generar_contrato

from core.views.rrhh.vacaciones import solicitud_vacaciones, vacaciones_home, vacaciones, crear_vacacion, vacaciones_empleado

urlpatterns = [
    path('admin/', admin.site.urls),

    # HOME
    path('', inicio),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),

    # CAJA MENOR
    path('caja-menor/', caja_menor, name='caja_menor'),
    path('caja-menor/<int:id>/', detalle_caja, name='detalle_caja'),
    path('caja-menor/<int:id>/agregar/', agregar_movimiento, name='agregar_movimiento'),
    path('movimiento/<int:id>/eliminar/', eliminar_movimiento, name='eliminar_movimiento'),
    path('movimiento/<int:id>/editar/', editar_movimiento, name='editar_movimiento'),

    # ACTAS
    path('actas/', actas, name='actas'),
    path('actas/crear/', crear_acta, name='crear_acta'),
    path('actas/<int:id>/', detalle_acta, name='detalle_acta'),
    path('actas/<int:id>/editar/', editar_acta, name='editar_acta'),
    path('actas/<int:id>/eliminar/', eliminar_acta, name='eliminar_acta'),

    # INDICADORES
    path('indicadores/', indicadores, name='indicadores'),
    path('indicadores/crear/', crear_indicador, name='crear_indicador'),
    path('indicadores/<int:id>/', detalle_indicador, name='detalle_indicador'),
    path('indicadores/<int:id>/agregar-seguimiento/', agregar_seguimiento, name='agregar_seguimiento'),
    path('indicadores/<int:id>/editar/', editar_indicador, name='editar_indicador'),
    path('indicadores/<int:id>/eliminar/', eliminar_indicador, name='eliminar_indicador'),
    path('seguimiento/<int:id>/editar/', editar_seguimiento, name='editar_seguimiento'),
    path('seguimiento/<int:id>/eliminar/', eliminar_seguimiento, name='eliminar_seguimiento'),

    # FACTURACIÓN
    path('facturacion/', facturacion, name='facturacion'),
    path('facturacion/crear-proyecto/', crear_proyecto, name='crear_proyecto'),
    path('facturacion/registrar/', registrar_facturacion, name='registrar_facturacion'),
    path('facturacion/<int:id>/editar/', editar_facturacion, name='editar_facturacion'),
    path('facturacion/<int:id>/eliminar/', eliminar_facturacion, name='eliminar_facturacion'),

    # RRHH
    path('rrhh/', rrhh_home, name='rrhh'),
    path('rrhh/empleados/', empleados, name='empleados'),
    path('rrhh/empleados/crear/', crear_empleado, name='crear_empleado'),
    path('rrhh/empleados/<int:id>/', detalle_empleado, name='detalle_empleado'),
    path('rrhh/empleados/<int:id>/eliminar/', eliminar_empleado, name='eliminar_empleado'),

    # DOTACIÓN / EQUIPOS
    path('rrhh/empleados/<int:id>/dotacion/', agregar_dotacion, name='agregar_dotacion'),
    path('rrhh/empleados/<int:id>/asignar-equipo/', asignar_equipo, name='asignar_equipo'),
    path('rrhh/equipos/<int:id>/eliminar/', eliminar_equipo, name='eliminar_equipo'),
    path('rrhh/equipos/<int:id>/editar/', editar_equipo, name='editar_equipo'),
    path('rrhh/empleados/<int:id>/acta_equipos/', acta_entrega_equipos, name='acta_entrega_equipos'),

    # INVENTARIO
    path('rrhh/inventario/', inventario_equipos, name='inventario_equipos'),
    path('rrhh/inventario/crear/', crear_equipo_inventario, name='crear_equipo_inventario'),
    path('rrhh/inventario/<int:id>/editar/', editar_equipo_inventario, name='editar_equipo_inventario'),
    path('rrhh/inventario/<int:id>/eliminar/', eliminar_equipo_inventario, name='eliminar_equipo_inventario'),

    # DOCUMENTOS
    path('rrhh/empleados/<int:id>/subir-documento/', subir_documento, name='subir_documento'),
    path('rrhh/documentos/<int:id>/eliminar/', eliminar_documento, name='eliminar_documento'),

    # DOCUMENTOS PDF/WORD
    path('rrhh/empleados/<int:id>/contrato/', generar_contrato, name='generar_contrato'),
    path('rrhh/empleados/<int:id>/certificacion/', certificacion_laboral, name='certificacion_laboral'),

    # PERMISOS
    path('rrhh/<int:id>/permiso/', permiso_laboral, name='permiso_laboral'),

    # VACACIONES
    path('rrhh/empleados/<int:id>/vacaciones/', vacaciones_empleado, name='vacaciones_empleado'),
    path('rrhh/vacaciones/', vacaciones, name='vacaciones'),
    path('rrhh/vacaciones/crear/', crear_vacacion, name='crear_vacacion'),
    path('rrhh/empleados/<int:id>/vacaciones/crear/', crear_vacacion, name='crear_vacacion_empleado'),
    path('rrhh/vacaciones/<int:id>/solicitud/', solicitud_vacaciones, name='solicitud_vacaciones'),
]

# =========================
# 📁 MEDIA FILES
# =========================
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)