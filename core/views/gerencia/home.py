from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import IndicadorEstrategico, ActaJuntaDirectiva, ProyectoFacturacion, SeguimientoFacturacion


@login_required
def gerencia_home(request):
    """
    Vista principal del Módulo de Gerencia & Gobernanza.
    Centraliza Actas de Junta Directiva, Indicadores Estratégicos y Facturación.
    """
    try:
        total_actas = ActaJuntaDirectiva.objects.count()
    except Exception:
        total_actas = 0

    try:
        total_indicadores = IndicadorEstrategico.objects.count()
    except Exception:
        total_indicadores = 0

    try:
        total_proyectos_facturacion = ProyectoFacturacion.objects.filter(activo=True).count()
        total_seguimientos_facturacion = SeguimientoFacturacion.objects.count()
    except Exception:
        total_proyectos_facturacion = 0
        total_seguimientos_facturacion = 0

    return render(
        request,
        'gerencia/gerencia_home.html',
        {
            'total_actas': total_actas,
            'total_indicadores': total_indicadores,
            'total_proyectos_facturacion': total_proyectos_facturacion,
            'total_seguimientos_facturacion': total_seguimientos_facturacion,
        }
    )


@login_required
def plan_estrategico(request):
    """
    Visor oficial del Plan Estratégico Corporativo 2026–2030 (GR-PL-01).
    """
    contexto = {
        'empresa': "COINTECA S.A.S. – INGENIERÍA",
        'horizonte': "2026 – 2030",
        'codigo_documento': "GR-PL-01",
        'mision': (
            "COINTECA S.A.S. cuya razón de ser es contribuir y lograr que nuestro portafolio de servicios "
            "cumpla con la más alta calidad, garantizando una excelente labor en el sector eléctrico mediante "
            "la transferencia del conocimiento, productividad y competitividad. Obteniendo así un bienestar "
            "socioeconómico, cultural y ambiental para nuestros clientes y colaboradores."
        ),
        'vision': (
            "COINTECA S.A.S. quiere ser una reconocida empresa moderna de servicios de ingeniería eléctrica, "
            "con equipos y talento humano calificado que brinden soluciones eficaces, eficientes e idóneas para "
            "las necesidades del sector eléctrico a través de una cultura de mejoramiento continuo e innovación "
            "con aplicaciones tecnológicas de equipos, elementos de protección, control y uso eficiente de los "
            "recursos energéticos."
        ),
        'valores': [
            {
                'titulo': "Excelencia Técnica",
                'icono': "⚡",
                'color': "blue",
                'descripcion': "Rigor en ingeniería eléctrica, cumplimiento estricto de RETIE, NTC 2050 e ISO 50001 en cada obra."
            },
            {
                'titulo': "Ética y Transparencia",
                'icono': "⚖️",
                'color': "indigo",
                'descripcion': "Integridad y claridad en contratos, actas de liquidación bilateral y relaciones con clientes y aliados."
            },
            {
                'titulo': "Responsabilidad",
                'icono': "🛡️",
                'color': "emerald",
                'descripcion': "Compromiso con la seguridad de nuestros colaboradores, bienestar de las comunidades y cuidado del entorno."
            },
            {
                'titulo': "Orientación al Cliente",
                'icono': "🎯",
                'color': "amber",
                'descripcion': "Respuestas ágiles, soluciones idóneas y acompañamiento técnico que maximizan la eficiencia energética."
            },
        ],
        'pilares': [
            {
                'pilar': "Financiero",
                'meta': "Margen por proyecto > 25% y eficacia de recaudo > 90%",
                'foco': "Sostenibilidad, control de costos operativos y optimización de capital de trabajo."
            },
            {
                'pilar': "Comercial & Expansión",
                'meta': "Tasa de cierre solar 15% e incremento del 10% en ticket promedio",
                'foco': "Penetración en proyectos solares fotovoltaicos, redes de distribución y alumbrado público."
            },
            {
                'pilar': "Operativo & Calidad",
                'meta': "100% éxito RETIE y eficiencia en redes > 0.95",
                'foco': "Cero hallazgos en terreno, digitalización de poste a poste y control estricto de materiales."
            },
            {
                'pilar': "Talento & Aprendizaje",
                'meta': "40 horas de capacitación técnica semestral por ingeniero",
                'foco': "Actualización en normativas, seguridad en alturas y tecnologías de vanguardia."
            },
        ]
    }
    return render(request, 'gerencia/plan_estrategico.html', contexto)


@login_required
def descargar_plan_estrategico(request):
    """
    Descarga el documento Word original del Plan Estratégico Corporativo (GR-PL-01).
    """
    import os
    from django.conf import settings
    from django.http import FileResponse, Http404

    ruta = os.path.join(settings.BASE_DIR, 'plantillas_word', 'plan_estrategico_corporativo.docx')
    if not os.path.exists(ruta):
        raise Http404("El archivo del Plan Estratégico no se encuentra disponible.")

    return FileResponse(
        open(ruta, 'rb'),
        as_attachment=True,
        filename="GR-PL-01_Plan_Estrategico_Corporativo_Cointeca_2026_2030.docx"
    )


