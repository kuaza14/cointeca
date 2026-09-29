"""
Middleware de Control de Acceso por Módulos para COINTECA S.A.S.
Intercepta solicitudes entrantes y asegura que cada usuario solo acceda a los módulos permitidos para su rol.
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from core.permisos import verificar_acceso_ruta, obtener_permisos_usuario


class ModuloPermisosMiddleware:
    """
    Middleware que valida que el usuario autenticado tenga los permisos
    necesarios para el módulo al que intenta acceder.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas exentas de validación de roles
        path = request.path
        if (
            path.startswith('/static/')
            or path.startswith('/media/')
            or path.startswith('/admin/')
            or path in ('/', '/login/', '/logout/', '/dashboard/')
        ):
            return self.get_response(request)

        # Si el usuario está autenticado, validar permisos de ruta
        if hasattr(request, 'user') and request.user.is_authenticated:
            permitido, nombre_modulo = verificar_acceso_ruta(request.user, path)
            if not permitido:
                # Si es una petición AJAX o API, retornar 403 Forbidden en JSON
                if (
                    request.headers.get('x-requested-with') == 'XMLHttpRequest'
                    or 'api' in path
                ):
                    return JsonResponse(
                        {'error': f'Acceso denegado: no tienes permisos para {nombre_modulo}.'},
                        status=403
                    )

                # Notificación visual para navegación normal
                permisos = obtener_permisos_usuario(request.user)
                messages.warning(
                    request,
                    f"⛔ Acceso restringido: Tu cuenta ({request.user.username} · {permisos['rol_principal']}) no tiene permisos para acceder al módulo de {nombre_modulo}."
                )
                return redirect('dashboard')

        return self.get_response(request)
