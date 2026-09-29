from core.views.alertas import obtener_alertas_vacaciones
from core.permisos import obtener_permisos_usuario


def alertas(request):
    return obtener_alertas_vacaciones()


def permisos_usuario(request):
    """
    Inyecta en todas las plantillas las variables de permisos del usuario:
    - puede_ver_gerencia
    - puede_ver_rrhh
    - puede_ver_ingenieria
    - puede_ver_logistica
    - puede_ver_contabilidad
    - rol_principal
    """
    if hasattr(request, 'user'):
        return obtener_permisos_usuario(request.user)
    return {}