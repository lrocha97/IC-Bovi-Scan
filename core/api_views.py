"""
Endpoints da API REST para o aplicativo core (IC-Bovi-Scan).

Fornece endpoints para processamento biométrico de bovinos, integrando
a camada de serviços de IA ao banco de dados e à documentação Swagger.
"""

import io
import logging
from decimal import Decimal
from django.core.files.base import ContentFile
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BovineAnalysis
from .serializers import (
    BovineAnalysisRequestSerializer,
    BovineAnalysisResponseSerializer,
)
from .services.inference_service import BovineInferenceService

logger = logging.getLogger(__name__)


class BovineAnalysisAPIView(APIView):
    """
    Endpoint principal para análise biométrica e estimativa de peso corporal de bovinos.

    Recebe uma imagem via requisição multipart/form-data, orquestra o pipeline
    de inteligência artificial (segmentação UNet + regressão EfficientNetB0),
    persiste os dados e imagens no banco e responde com JSON estruturado.
    """

    parser_classes = [MultiPartParser]

    @extend_schema(
        summary="Análise biométrica e pesagem de bovino",
        description=(
            "Recebe uma fotografia de perfil lateral de um bovino, submete a imagem "
            "ao modelo UNet (segmentação corporal) e ao modelo regressor de peso, "
            "salva os registros e arquivos em disco/banco e retorna as métricas "
            "juntamente com as máscaras codificadas em Base64 e URLs das mídias."
        ),
        request={
            'multipart/form-data': BovineAnalysisRequestSerializer,
        },
        responses={
            status.HTTP_201_CREATED: BovineAnalysisResponseSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Dados inválidos ou imagem corrompida/incompatível."
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Erro interno durante a inferência dos modelos de IA."
            ),
        },
        tags=["Biometria Bovina"]
    )
    def post(self, request, *args, **kwargs):
        """
        Processa o upload da imagem e retorna as predições de peso e máscara.
        """
        serializer = BovineAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']

        try:
            # 1. Executa a pipeline completa de inferência
            service = BovineInferenceService()
            inference_result = service.run_pipeline(image_file)

            # 2. Converte a máscara gerada para bytes para salvar no modelo Django
            mask_buffer = io.BytesIO()
            inference_result.mask_image_pil.save(mask_buffer, format='PNG')
            mask_filename = f"mask_{image_file.name.rsplit('.', 1)[0]}.png"
            mask_content = ContentFile(mask_buffer.getvalue(), name=mask_filename)

            # 3. Persiste a análise no banco de dados
            analysis = BovineAnalysis.objects.create(
                original_image=image_file,
                mask_image=mask_content,
                estimated_weight=Decimal(str(inference_result.estimated_weight_kg)),
                mask_area_percentage=inference_result.mask_area_percentage,
                confidence_score=inference_result.confidence_score,
                inference_time_ms=inference_result.inference_time_ms
            )

            # 4. Serializa a resposta combinando dados do banco e imagens Base64
            response_serializer = BovineAnalysisResponseSerializer(analysis)
            response_data = dict(response_serializer.data)
            response_data['mask_base64'] = inference_result.mask_base64
            response_data['overlay_base64'] = inference_result.overlay_base64
            response_data['device_used'] = inference_result.device_used

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as exc:
            logger.exception("Falha ao processar análise do bovino: %s", exc)
            return Response(
                {"error": "Falha no processamento da imagem pela IA.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
