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

