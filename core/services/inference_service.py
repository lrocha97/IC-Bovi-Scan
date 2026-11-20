"""
Serviço orquestrador de inferência de Inteligência Artificial.

Coordena o fluxo ponta a ponta: recebe a imagem de entrada, executa o
pré-processamento, dispara a inferência na rede UNet e no regressor, calcula
as métricas biométricas e formata a resposta final.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image

from .image_processor import ImageProcessor
from .model_loader import ModelManager

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """
    Estrutura de dados contendo o resultado consolidado da inferência.
    """
    estimated_weight_kg: float
    mask_area_percentage: float
    aspect_ratio: float
    confidence_score: float
    inference_time_ms: int
    mask_image_pil: Image.Image
    overlay_image_pil: Image.Image
    mask_base64: str
    overlay_base64: str
    device_used: str


class BovineInferenceService:
    """
    Orquestrador responsável pelo pipeline de visão computacional e pesagem.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None) -> None:
        """Inicializa o serviço obtendo o gerenciador de modelos Singleton."""
        self.manager = model_manager or ModelManager()

    def run_pipeline(
        self,
        image_input: Any,
        custom_metadata: Optional[Dict[str, float]] = None
    ) -> InferenceResult:
        """
        Executa a pipeline completa de segmentação e estimativa de peso.

        Passos executados:
        1. Pré-processamento e normalização da imagem para tensor (1, 224, 224, 3).
        2. Inferência na rede UNet para geração da máscara da silhueta.
        3. Extração de métricas morfológicas (área em % e proporção de aspecto).
        4. Inferência no modelo regressor combinando imagem e vetor de características.
        5. Geração de sobreposição visual (overlay) e codificação Base64.
        6. Mensuração da latência em milissegundos.

        Args:
            image_input: Arquivo de imagem enviado (bytes ou UploadedFile).
            custom_metadata: Dicionário opcional com metadados adicionais.

        Returns:
            InferenceResult: Objeto estruturado com todos os resultados preditos.
        """
        start_time = time.perf_counter()

        # 1. Recupera os modelos carregados em memória RAM/VRAM
        seg_model, reg_model = self.manager.get_models()

        # 2. Pré-processamento da imagem
        batch_tensor, resized_pil = ImageProcessor.load_and_preprocess(image_input)

        # 3. Inferência de Segmentação (UNet)
        raw_mask_pred = seg_model.predict(batch_tensor, verbose=0)
        binary_mask, mask_pil = ImageProcessor.postprocess_mask(raw_mask_pred)
        metrics = ImageProcessor.calculate_metrics(binary_mask)

        # 4. Construção do vetor de metadados para o regressor (shape [1, 3])
        # Padrão: [fração da área da máscara, 0.0, 0.0]
        meta_vector = np.array(
            [[metrics['area_fraction'], 0.0, 0.0]],
            dtype=np.float32
        )

        # 5. Inferência de Regressão de Peso (EfficientNetB0)
        weight_pred = reg_model.predict(
            {'visual_input': batch_tensor, 'meta_input': meta_vector},
            verbose=0
        )
        estimated_weight = float(weight_pred[0][0])
        # Garante plausibilidade física (peso não negativo)
        estimated_weight = max(0.0, round(estimated_weight, 2))

        # 6. Cálculo de confiança e imagens derivadas
        confidence = 94.0 if metrics['area_percentage'] > 5.0 else 50.0
        overlay_pil = ImageProcessor.create_mask_overlay(resized_pil, binary_mask)
        mask_base64 = ImageProcessor.to_base64_data_uri(mask_pil)
        overlay_base64 = ImageProcessor.to_base64_data_uri(overlay_pil)

        # 7. Mensuração do tempo total de execução em milissegundos
        total_time_ms = int((time.perf_counter() - start_time) * 1000)

        return InferenceResult(
            estimated_weight_kg=estimated_weight,
            mask_area_percentage=metrics['area_percentage'],
            aspect_ratio=metrics['aspect_ratio'],
            confidence_score=confidence,
            inference_time_ms=total_time_ms,
            mask_image_pil=mask_pil,
            overlay_image_pil=overlay_pil,
            mask_base64=mask_base64,
            overlay_base64=overlay_base64,
            device_used=self.manager.device_info
        )
