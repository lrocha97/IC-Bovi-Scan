"""
Roteamento global de URLs do projeto IC-Bovi-Scan.

Mapeia as rotas administrativas, endpoints do aplicativo core,
documentação OpenAPI/Swagger e arquivos de mídia em ambiente de desenvolvimento.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Painel Administrativo
    path('admin/', admin.site.urls),

    # Documentação Interativa da API (Swagger / OpenAPI 3)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Rotas da Aplicação Core
    path('', include('core.urls')),
]

# Servir arquivos de mídia (uploads e máscaras) em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
