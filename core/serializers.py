"""
Serializadores do Django REST Framework para a API do IC-Bovi-Scan.

Define a validação dos dados de entrada (upload de imagem) e a estrutura
do payload JSON de resposta com métricas biométricas e codificações Base64.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import BovineAnalysis


@extend_schema_field(OpenApiTypes.BINARY)
class UploadedImageField(serializers.ImageField):
    """
    Campo customizado de upload de imagem.
    Força a anotação OpenAPI como tipo 'binary' para habilitar o seletor de arquivos no Swagger UI.
    """
    pass


class BovineAnalysisRequestSerializer(serializers.Serializer):
    """
    Serializador para validação da requisição de análise.
    Espera uma imagem de perfil lateral de bovino enviada via multipart/form-data.
    """

    image = UploadedImageField(
        required=True,
        help_text="Arquivo de imagem do bovino (formatos aceitos: JPEG, PNG, WebP)."
    )


class BovineAnalysisResponseSerializer(serializers.ModelSerializer):
    """
    Serializador para o payload de resposta da análise biométrica.
    Retorna os dados cadastrados no banco de dados, URLs e representações Base64.
    """

    mask_base64 = serializers.CharField(
        read_only=True,
        help_text="Máscara de segmentação binária codificada em Data URI Base64."
    )

    overlay_base64 = serializers.CharField(
        read_only=True,
        help_text="Sobreposição visual colorida da silhueta sobre a foto em Data URI Base64."
    )

    device_used = serializers.CharField(
        read_only=True,
        required=False,
        help_text="Dispositivo computacional utilizado na inferência (GPU ou CPU)."
    )

    class Meta:
        model = BovineAnalysis
        fields = [
            'id',
            'uuid',
            'estimated_weight',
            'mask_area_percentage',
            'confidence_score',
            'inference_time_ms',
            'original_image',
            'mask_image',
            'mask_base64',
            'overlay_base64',
            'device_used',
            'created_at',
        ]
        read_only_fields = fields
