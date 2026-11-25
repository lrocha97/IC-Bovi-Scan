"""
Roteamento interno de URLs do aplicativo core.

Define as rotas de interface de usuário e os endpoints da API REST
para processamento biométrico de bovinos.
"""

from django.urls import path
from . import api_views, views

app_name = 'core'

urlpatterns = [
    # Interface Gráfica Web
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bovine/<uuid:uuid>/', views.bovine_detail, name='bovine-detail'),

    # Endpoints da API REST (v1)
    path(
        'api/v1/cattle/analyze/',
        api_views.BovineAnalysisAPIView.as_view(),
        name='cattle-analyze'
    ),
]
