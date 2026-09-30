"""
Sistema de Control de Acceso Basado en Roles (RBAC) para COINTECA S.A.S.

Reglas de Acceso del Negocio:
1. Gerencia / Superusuario (gerente, admin, grupo 'Gerencia'):
   - Acceso total e irrestricto a todos los módulos.
2. RRHH (rrhh, grupo 'RRHH'):
   - Acceso exclusivo a Recursos Humanos (/rrhh/).
3. Ingeniería y Logística (ingenieria, logistica, grupos 'ingenieria', 'Logistica'):
   - Comparten acceso mutuo completo a Ingeniería (/ingenieria/) y Logística (/logistica/).
4. Contabilidad (contabilidad, grupo 'Contabilidad'):
   - Acceso exclusivo a Contabilidad y Caja Menor (/caja-menor/, /movimiento/).
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden


def normalizar_texto(texto):
    """Convierte a minúsculas y remueve acentos."""
    if not texto:
        return ""
    t = str(texto).strip().lower()
    acentos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
    for con_acento, sin_acento in acentos.items():
        t = t.replace(con_acento, sin_acento)
    return t


def obtener_permisos_usuario(user):
    """
    Retorna un diccionario completo con los permisos de acceso por módulo del usuario.
    """
    if not user or not user.is_authenticated:
        return {
            'es_autenticado': False,
            'es_gerencia': False,
            'puede_ver_gerencia': False,
            'puede_ver_rrhh': False,
            'puede_ver_ingenieria': False,
            'puede_ver_logistica': False,
            'puede_ver_contabilidad': False,
            'rol_principal': 'Invitado',
            'roles': set(),
        }

    if hasattr(user, '_permisos_cache'):
        return user._permisos_cache

    # Grupos del usuario en minúsculas y sin acentos
    grupos_raw = list(user.groups.values_list('name', flat=True))
    roles = {normalizar_texto(g) for g in grupos_raw}

    username_norm = normalizar_texto(user.username)

    # Identificación de roles
    es_gerencia = (
        user.is_superuser
        or 'gerencia' in roles
        or username_norm in ('gerente', 'admin', 'admin_test')
    )
    es_rrhh = 'rrhh' in roles or username_norm == 'rrhh'
    es_ingenieria = 'ingenieria' in roles or username_norm == 'ingenieria'
    es_logistica = 'logistica' in roles or username_norm == 'logistica'
    es_contabilidad = 'contabilidad' in roles or username_norm == 'contabilidad'

    if es_gerencia:
        puede_gerencia = True
        puede_rrhh = True
        puede_ingenieria = True
        puede_logistica = True
        puede_contabilidad = True
        rol_nombre = 'Gerencia General'
    else:
        puede_gerencia = False
        puede_rrhh = es_rrhh
        # Ingeniería y Logística comparten acceso completo entre sí
        puede_ingenieria = es_ingenieria or es_logistica
        puede_logistica = es_ingenieria or es_logistica
        puede_contabilidad = es_contabilidad

        if es_rrhh:
            rol_nombre = 'Recursos Humanos'
        elif es_ingenieria and es_logistica:
            rol_nombre = 'Ingeniería & Logística'
        elif es_ingenieria:
            rol_nombre = 'Ingeniería'
        elif es_logistica:
            rol_nombre = 'Logística'
        elif es_contabilidad:
            rol_nombre = 'Contabilidad'
        else:
            rol_nombre = 'Colaborador'

    resultado = {
        'es_autenticado': True,
        'es_gerencia': es_gerencia,
        'puede_ver_gerencia': puede_gerencia,
        'puede_ver_rrhh': puede_rrhh,
        'puede_ver_ingenieria': puede_ingenieria,
        'puede_ver_logistica': puede_logistica,
        'puede_ver_contabilidad': puede_contabilidad,
        'rol_principal': rol_nombre,
        'roles': roles,
    }
    try:
        user._permisos_cache = resultado
    except Exception:
        pass
    return resultado


# Mapeo de prefijos de URL a claves de permisos y nombres de módulo legibles
RUTAS_MODULOS = [
    {
        'clave': 'gerencia',
        'nombre': 'Gerencia y Gobernanza',
        'prefijos': ['/gerencia/', '/actas/', '/indicadores/', '/seguimiento/', '/facturacion/'],
        'permiso_requerido': 'puede_ver_gerencia',
    },
    {
        'clave': 'rrhh',
        'nombre': 'Recursos Humanos',
        'prefijos': ['/rrhh/'],
        'permiso_requerido': 'puede_ver_rrhh',
    },
    {
        'clave': 'ingenieria',
        'nombre': 'Ingeniería',
        'prefijos': ['/ingenieria/'],
        'permiso_requerido': 'puede_ver_ingenieria',
    },
    {
        'clave': 'logistica',
        'nombre': 'Logística',
        'prefijos': ['/logistica/'],
        'permiso_requerido': 'puede_ver_logistica',
    },
    {
        'clave': 'contabilidad',
        'nombre': 'Contabilidad / Caja Menor',
        'prefijos': ['/caja-menor/', '/movimiento/'],
        'permiso_requerido': 'puede_ver_contabilidad',
    },
]


def verificar_acceso_ruta(user, path):
    """
    Verifica si el usuario tiene permiso para acceder a la ruta especificada.
    Retorna una tupla: (permitido: bool, nombre_modulo: str | None)
    """
    if not user or not user.is_authenticated:
        # Los no autenticados son gestionados por @login_required
        return True, None

    permisos = obtener_permisos_usuario(user)

    # Superusuarios o Gerencia siempre tienen acceso
    if permisos['puede_ver_gerencia']:
        return True, None

    # Normalizar ruta para comparación
    path_normalizada = path.lower()

    for modulo in RUTAS_MODULOS:
        for prefijo in modulo['prefijos']:
            prefijo_sin_barra = prefijo.rstrip('/')
            if path_normalizada.startswith(prefijo) or path_normalizada == prefijo_sin_barra:
                tiene_permiso = permisos.get(modulo['permiso_requerido'], False)
                if not tiene_permiso:
                    return False, modulo['nombre']
                return True, None

    # Rutas públicas o compartidas (dashboard, login, media, static, etc.)
    return True, None


def requiere_modulo(clave_modulo):
    """
    Decorador para proteger vistas específicas de Django.
    Ejemplo: @requiere_modulo('rrhh')
    """
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            permisos = obtener_permisos_usuario(request.user)
            campo_permiso = f"puede_ver_{clave_modulo}"
            if not permisos.get(campo_permiso, False):
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Acceso no autorizado.'}, status=403)
                messages.warning(
                    request,
                    f"⛔ Acceso denegado: No tienes permisos para acceder al módulo de {clave_modulo.capitalize()}."
                )
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorador
