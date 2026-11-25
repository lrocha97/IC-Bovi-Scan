"""
Views de renderização das páginas web do aplicativo core.

A análise em si é feita pela API REST (api_views.py); estas views apenas
entregam as páginas que consomem a API e exibem o histórico por bovino.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, render

from .models import Bovine, BovineAnalysis


def history_access(view):
    """Exige login para o histórico quando a inferência também exige autenticação."""
    if getattr(settings, 'REQUIRE_AUTH_FOR_INFERENCE', True):
        return login_required(view)
    return view


def _processed_analyses():
    """Análises concluídas, da mais recente para a mais antiga."""
    return BovineAnalysis.objects.filter(estimated_weight__isnull=False).order_by('-created_at')


def index(request):
    """Página inicial com upload da imagem, nome do bovino e resultado da IA."""
    return render(request, 'core/index.html')


@history_access
def dashboard(request):
    """Lista os bovinos identificados com a última pesagem de cada um."""
    bovines = (
        Bovine.objects
        .annotate(total=Count('analyses'))
        .filter(total__gt=0)
        .prefetch_related(Prefetch('analyses', queryset=_processed_analyses(), to_attr='ordered_analyses'))
    )
    items = [
        {'bovine': b, 'count': len(b.ordered_analyses), 'latest': b.ordered_analyses[0]}
        for b in bovines if b.ordered_analyses
    ]
    items.sort(key=lambda i: i['latest'].created_at, reverse=True)
    return render(request, 'core/dashboard.html', {'items': items})


@history_access
def bovine_detail(request, uuid):
    """Histórico completo de um bovino: fotos ao longo do tempo e gráfico de peso."""
    bovine = get_object_or_404(Bovine, uuid=uuid)
    analyses = list(bovine.analyses.filter(estimated_weight__isnull=False).order_by('created_at'))
    chart_data = [
        {
            'date': timezone_label(a.created_at),
            'timestamp': a.created_at.isoformat(),
            'weight': float(a.estimated_weight),
        }
        for a in analyses
    ]
    return render(request, 'core/bovine_detail.html', {
        'bovine': bovine,
        'analyses': list(reversed(analyses)),  # mais recente primeiro na galeria
        'chart_data': chart_data,
    })


def timezone_label(value):
    """Formata a data no fuso configurado (dd/mm/aaaa HH:MM)."""
    from django.utils import timezone
    return timezone.localtime(value).strftime('%d/%m/%Y %H:%M')
