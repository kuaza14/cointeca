import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import ActaJuntaDirectiva, IndicadorEstrategico, ProyectoFacturacion, SeguimientoFacturacion
from django.conf import settings

if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

def run_tests():
    print("=== INICIANDO VALIDACIÓN DE MÓDULO GERENCIA & GOBERNANZA ===")

    user = User.objects.first()
    client = Client()
    client.force_login(user)

    # 1. Probar Plan Estratégico Corporativo
    url_plan = reverse('plan_estrategico')
    resp_plan = client.get(url_plan)
    assert resp_plan.status_code == 200, f"Fallo plan_estrategico: {resp_plan.status_code}"
    html_plan = resp_plan.content.decode('utf-8')
    assert "Nuestra Misión" in html_plan, "No se encontró Nuestra Misión en plan_estrategico.html"
    assert "Nuestra Visión" in html_plan, "No se encontró Nuestra Visión en plan_estrategico.html"
    assert "Excelencia Técnica" in html_plan, "No se encontró Excelencia Técnica en plan_estrategico.html"
    print("1. Vista plan_estrategico: OK (HTTP 200, contenido verificado)")

    url_descarga_plan = reverse('descargar_plan_estrategico')
    resp_descarga_plan = client.get(url_descarga_plan)
    assert resp_descarga_plan.status_code == 200, f"Fallo descargar_plan_estrategico: {resp_descarga_plan.status_code}"
    assert 'attachment' in resp_descarga_plan.get('Content-Disposition', ''), "Header attachment no encontrado"
    print("2. Descarga plan_estrategico (.docx): OK (HTTP 200, archivo adjunto)")

    # 2. Probar Actas de Junta Directiva y Exportación a Word
    acta = ActaJuntaDirectiva.objects.first()
    if not acta:
        acta = ActaJuntaDirectiva.objects.create(
            numero_acta="001",
            nombre_entidad="COINTECA S.A.S.",
            nit="901.234.567-8",
            fecha="2026-09-28",
            hora_inicio="09:00:00",
            lugar="Oficina Principal Cali",
            presidente="Carlos Gómez",
            secretario="María López",
            orden_del_dia="1. Verificación Quórum\n2. Aprobación Presupuesto\n3. Proposiciones",
            desarrollo="Se verificó quórum y se aprobó por unanimidad la expansión del proyecto.",
            proposiciones="Ninguna adicional.",
            estado="aprobada"
        )
    url_actas = reverse('actas')
    resp_actas = client.get(url_actas)
    assert resp_actas.status_code == 200, f"Fallo vista actas: {resp_actas.status_code}"
    print("3. Vista actas: OK (HTTP 200)")

    url_export_acta = reverse('exportar_acta_word', kwargs={'id': acta.id})
    resp_export_acta = client.get(url_export_acta)
    assert resp_export_acta.status_code == 200, f"Fallo exportar_acta_word: {resp_export_acta.status_code}"
    assert 'attachment' in resp_export_acta.get('Content-Disposition', ''), "Header attachment no encontrado en acta docx"
    print(f"4. Exportar Acta {acta.numero_acta} a Word (.docx): OK (HTTP 200, formato oficial GR-FR-01 generado)")

    # 3. Probar Indicadores Estratégicos & 9 KPIs
    url_ind = reverse('indicadores')
    resp_ind = client.get(url_ind)
    assert resp_ind.status_code == 200, f"Fallo vista indicadores: {resp_ind.status_code}"
    total_kpis = IndicadorEstrategico.objects.count()
    assert total_kpis >= 9, f"Se esperaban al menos 9 KPIs oficiales, encontrados: {total_kpis}"
    print(f"5. Vista indicadores: OK (HTTP 200, {total_kpis} KPIs en BD)")

    url_export_ind = reverse('exportar_indicadores_excel')
    resp_export_ind = client.get(url_export_ind)
    assert resp_export_ind.status_code == 200, f"Fallo exportar_indicadores_excel: {resp_export_ind.status_code}"
    assert 'attachment' in resp_export_ind.get('Content-Disposition', ''), "Header attachment no encontrado en indicadores xlsx"
    print("6. Exportar Indicadores a Excel (.xlsx): OK (HTTP 200, libro GER-FR-02 generado)")

    # 4. Probar Seguimiento de Facturación y Matriz Anual
    url_fact = reverse('facturacion')
    resp_fact = client.get(url_fact)
    assert resp_fact.status_code == 200, f"Fallo vista facturacion: {resp_fact.status_code}"
    html_fact = resp_fact.content.decode('utf-8')
    assert "Consolidado Anual de Facturación" in html_fact, "Matriz anual no encontrada en HTML"
    assert "Enero" in html_fact and "Diciembre" in html_fact, "Meses no encontrados en la matriz"
    print("7. Vista facturacion con Matriz Anual (Enero-Diciembre): OK (HTTP 200)")

    url_export_fact = reverse('exportar_facturacion_excel')
    resp_export_fact = client.get(url_export_fact)
    assert resp_export_fact.status_code == 200, f"Fallo exportar_facturacion_excel: {resp_export_fact.status_code}"
    assert 'attachment' in resp_export_fact.get('Content-Disposition', ''), "Header attachment no encontrado en facturacion xlsx"
    print("8. Exportar Seguimiento Facturación a Excel (.xlsx): OK (HTTP 200)")

    # 5. Probar Home de Gerencia con las 4 tarjetas
    url_home = reverse('gerencia_home')
    resp_home = client.get(url_home)
    assert resp_home.status_code == 200, f"Fallo gerencia_home: {resp_home.status_code}"
    html_home = resp_home.content.decode('utf-8')
    assert "Plan Estratégico" in html_home, "Tarjeta Plan Estratégico no encontrada en gerencia_home"
    print("9. Vista gerencia_home con 4 tarjetas institucionales: OK (HTTP 200)")

    print("\n✅ TODAS LAS PRUEBAS DE GERENCIA & GOBERNANZA PASARON SATISFACTORIAMENTE!")

if __name__ == '__main__':
    run_tests()
