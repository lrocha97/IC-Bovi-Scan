"""
Configuração do painel administrativo Django para o aplicativo core.

Permite que os pesquisadores visualizem o histórico de análises biométricas,
miniaturas das imagens originais e máscaras geradas, filtrando por data e peso.
"""

from django.contrib import admin
from django.utils.html import mark_safe
from .models import Bovine, BovineAnalysis


@admin.register(Bovine)
class BovineAdmin(admin.ModelAdmin):
    """Configuração administrativa para os bovinos identificados."""

    list_display = ('name', 'uuid', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('uuid', 'created_at')


@admin.register(BovineAnalysis)
class BovineAnalysisAdmin(admin.ModelAdmin):
    """
    Configuração administrativa para o modelo BovineAnalysis.
    Exibe miniaturas visuais e métricas no painel Django Admin.
    """

    list_display = (
        'id',
        'preview_original',
        'preview_mask',
        'estimated_weight_display',
        'mask_area_display',
        'inference_time_ms',
        'created_at',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'id',
        'uuid',
    )

    readonly_fields = (
        'uuid',
        'created_at',
        'updated_at',
        'preview_original_large',
        'preview_mask_large',
    )

    fields = (
        'uuid',
        'bovine',
        'original_image',
        'preview_original_large',
        'mask_image',
        'preview_mask_large',
        'estimated_weight',
        'mask_area_percentage',
        'confidence_score',
        'inference_time_ms',
        'created_at',
        'updated_at',
    )

    @admin.display(description="Foto Original")
    def preview_original(self, obj: BovineAnalysis):
        """Exibe miniatura da foto original na tabela de listagem."""
        if obj.original_image:
            return mark_safe(
                f'<img src="{obj.original_image.url}" style="max-height: 50px; border-radius: 4px;" alt="Original" />'
            )
        return "-"

    @admin.display(description="Máscara IA")
    def preview_mask(self, obj: BovineAnalysis):
        """Exibe miniatura da máscara na tabela de listagem."""
        if obj.mask_image:
            return mark_safe(
                f'<img src="{obj.mask_image.url}" style="max-height: 50px; border-radius: 4px; background: #000;" alt="Máscara" />'
            )
        return "-"

    @admin.display(description="Visualização Ampliada (Original)")
    def preview_original_large(self, obj: BovineAnalysis):
        """Exibe imagem original ampliada na página de detalhes."""
        if obj.original_image:
            return mark_safe(
                f'<img src="{obj.original_image.url}" style="max-height: 250px; border-radius: 8px;" alt="Original" />'
            )
        return "-"

    @admin.display(description="Visualização Ampliada (Máscara)")
    def preview_mask_large(self, obj: BovineAnalysis):
        """Exibe máscara ampliada na página de detalhes."""
        if obj.mask_image:
            return mark_safe(
                f'<img src="{obj.mask_image.url}" style="max-height: 250px; border-radius: 8px; background: #000;" alt="Máscara" />'
            )
        return "-"

    @admin.display(description="Peso (kg)")
    def estimated_weight_display(self, obj: BovineAnalysis):
        """Formata o peso estimado para exibição."""
        if obj.estimated_weight is not None:
            return f"{obj.estimated_weight:.2f} kg"
        return "Pendente"

    @admin.display(description="Área (%)")
    def mask_area_display(self, obj: BovineAnalysis):
        """Formata o percentual de área da máscara."""
        if obj.mask_area_percentage is not None:
            return f"{obj.mask_area_percentage:.1f}%"
        return "Pendente"
