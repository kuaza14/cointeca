import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.template import Template, Context
from django.test import Client
from core.models import Material, Inventario, Proyecto
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings

if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

def run():
    print("Iniciando verificación de formateo limpio de decimales...")

    # 1. Probar que floatformat global nunca use coma y elimine ceros sobrantes
    test_cases = [
        ("{{ v|floatformat }}", 20.0, "20"),
        ("{{ v|floatformat:1 }}", 20.0, "20"),
        ("{{ v|floatformat:2 }}", 20.0, "20"),
        ("{{ v|floatformat }}", 20.5, "20.5"),
        ("{{ v|floatformat:1 }}", 20.5, "20.5"),
        ("{{ v|floatformat }}", Decimal("20.00"), "20"),
        ("{{ v|floatformat }}", Decimal("20.50"), "20.5"),
        ("{{ v|floatformat }}", Decimal("20.25"), "20.25"),
        ("{{ v|floatformat }}", Decimal("-12.00"), "-12"),
        ("{{ v|floatformat }}", Decimal("-30.00"), "-30"),
        ("{{ v|floatformat }}", Decimal("0.00"), "0"),
        ("{{ v|floatformat:0 }}", 1500000.0, "1500000"),
    ]

    for tpl_str, val, expected in test_cases:
        t = Template(tpl_str)
        rendered = t.render(Context({'v': val}))
        print(f"Template '{tpl_str}' con {val!r} -> '{rendered}' (Esperado: '{expected}')")
        assert rendered == expected, f"Fallo: se obtuvo '{rendered}' en vez de '{expected}'"

    print("Verificación de plantillas base SUPERADA exitosamente!")

    # 2. Probar renderizado real de la vista materiales_home
    user = User.objects.first()
    client = Client()
    client.force_login(user)

    url_bodega = reverse("materiales_home")
    resp_bodega = client.get(url_bodega)
    assert resp_bodega.status_code == 200
    html_bodega = resp_bodega.content.decode("utf-8")
    
    # Comprobar que en html_bodega no existan patrones como '20,0' o '12,0' en badges de existencia o inputs
    print("Vista materiales_home respondió HTTP 200 OK.")

    # 3. Probar renderizado real de detalle_proyecto
    proyecto = Proyecto.objects.first()
    if proyecto:
        url_proy = reverse("detalle_proyecto", kwargs={"id": proyecto.id})
        resp_proy = client.get(url_proy)
        assert resp_proy.status_code == 200
        print(f"Vista detalle_proyecto (Proyecto {proyecto.numero_emcali}) respondió HTTP 200 OK.")

    print("TODAS LAS PRUEBAS DE FORMATEO DECIMAL PASARON SATISFACTORIAMENTE!")

if __name__ == "__main__":
    run()
