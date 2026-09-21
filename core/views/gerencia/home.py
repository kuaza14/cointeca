from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import IndicadorEstrategico, ActaJuntaDirectiva


@login_required
def gerencia_home(request):
    """
    Vista principal del Módulo de Gerencia & Gobernanza.
    Centraliza Actas de Junta Directiva e Indicadores Estratégicos.
    """
    try:
        total_actas = ActaJuntaDirectiva.objects.count()
    except Exception:
        total_actas = 0

    try:
        total_indicadores = IndicadorEstrategico.objects.count()
    except Exception:
        total_indicadores = 0

    return render(
        request,
        'gerencia/gerencia_home.html',
        {
            'total_actas': total_actas,
            'total_indicadores': total_indicadores,
        }
    )
