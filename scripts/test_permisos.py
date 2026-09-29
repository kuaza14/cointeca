from django.test import Client
from django.contrib.auth.models import User

users = {
    'gerente': User.objects.get(username='gerente'),
    'rrhh': User.objects.get(username='rrhh'),
    'ingenieria': User.objects.get(username='ingenieria'),
    'logistica': User.objects.get(username='logistica'),
    'contabilidad': User.objects.get(username='contabilidad'),
}

modules = {
    'gerencia': '/gerencia/',
    'rrhh': '/rrhh/empleados/',
    'ingenieria': '/ingenieria/',
    'logistica': '/logistica/',
    'contabilidad': '/caja-menor/',
}

matrix = {
    ('gerente', 'gerencia'): True,
    ('gerente', 'rrhh'): True,
    ('gerente', 'ingenieria'): True,
    ('gerente', 'logistica'): True,
    ('gerente', 'contabilidad'): True,

    ('rrhh', 'gerencia'): False,
    ('rrhh', 'rrhh'): True,
    ('rrhh', 'ingenieria'): False,
    ('rrhh', 'logistica'): False,
    ('rrhh', 'contabilidad'): False,

    ('ingenieria', 'gerencia'): False,
    ('ingenieria', 'rrhh'): False,
    ('ingenieria', 'ingenieria'): True,
    ('ingenieria', 'logistica'): True,
    ('ingenieria', 'contabilidad'): False,

    ('logistica', 'gerencia'): False,
    ('logistica', 'rrhh'): False,
    ('logistica', 'ingenieria'): True,
    ('logistica', 'logistica'): True,
    ('logistica', 'contabilidad'): False,

    ('contabilidad', 'gerencia'): False,
    ('contabilidad', 'rrhh'): False,
    ('contabilidad', 'ingenieria'): False,
    ('contabilidad', 'logistica'): False,
    ('contabilidad', 'contabilidad'): True,
}

all_passed = True
for (ukey, mkey), expected in matrix.items():
    u = users[ukey]
    url = modules[mkey]
    client = Client(HTTP_HOST='localhost')
    client.force_login(u)
    res = client.get(url)
    
    if expected:
        ok = (res.status_code == 200)
    else:
        ok = (res.status_code == 302 and res.url == '/dashboard/')
        
    status_label = 'PASS' if ok else 'FAIL'
    if not ok:
        all_passed = False
    redirect_info = f" -> {res.url}" if res.status_code == 302 else ""
    print(f"[{status_label}] User: {ukey:12} | Module: {mkey:12} | Expected: {str(expected):5} | Got: {res.status_code}{redirect_info}")

if all_passed:
    print("\n>>> ALL 25 PERMISSION COMBINATIONS PASSED PERFECTLY! <<<")
else:
    raise AssertionError("Some permission tests failed!")
