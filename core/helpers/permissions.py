from django.contrib.auth.models import Group


def es_gerencia(user):
    return user.is_authenticated and user.groups.filter(
        name="Gerencia"
    ).exists()


def es_rrhh(user):
    return user.is_authenticated and user.groups.filter(
        name="RRHH"
    ).exists()


def es_logistica(user):
    return user.is_authenticated and user.groups.filter(
        name="Logística"
    ).exists()


def es_contabilidad(user):
    return user.is_authenticated and user.groups.filter(
        name="Contabilidad"
    ).exists()


def es_superusuario(user):
    return user.is_authenticated and user.is_superuser

def puede_ver_rrhh(user):
    return (
        es_superusuario(user)
        or es_gerencia(user)
        or es_rrhh(user)
    )


def puede_ver_logistica(user):
    return (
        es_superusuario(user)
        or es_gerencia(user)
        or es_logistica(user)
    )


def puede_ver_contabilidad(user):
    return (
        es_superusuario(user)
        or es_gerencia(user)
        or es_contabilidad(user)
    )


def puede_ver_gerencia(user):
    return (
        es_superusuario(user)
        or es_gerencia(user)
    )