"""
Gerenciador e carregador Singleton de modelos de Inteligência Artificial.

Controla o ciclo de vida dos modelos Keras em memória RAM/VRAM,
garantindo que os pesos sejam carregados apenas uma vez durante
o ciclo de execução do backend e gerenciando o fallback entre GPU e CPU.
"""

import logging
import os
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Optional, Tuple

# Configurações de ambiente pré-carregamento do Keras/TensorFlow
os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import keras
import tensorflow as tf

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Controlador Singleton responsável pelo carregamento e acesso aos modelos Keras.

    Mantém em cache os modelos de segmentação (EfficientNetB4_UNet) e de
    regressão de peso (EfficientNetB0_SideProfile_Regressor), provendo acesso
    seguro entre múltiplas threads.
    """

    _instance: Optional['ModelManager'] = None
    _lock: threading.Lock = threading.Lock()

    _seg_model: Optional[keras.Model] = None
    _reg_model: Optional[keras.Model] = None

    _cache_dir: Optional[str] = None
    _device_info: str = "Unknown"

    def __new__(cls) -> 'ModelManager':
        """Implementação padrão do padrão Singleton com Thread Safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Configura os diretórios de cache temporário e verifica os aceleradores de hardware."""
        self._cache_dir = tempfile.mkdtemp(prefix="boviscan_models_")
        self._check_hardware()

    def _check_hardware(self) -> None:
        """
        Inspeciona os dispositivos físicos disponíveis (GPU/MPS/CPU).

        Registra em log a presença de aceleradores gráficos compatíveis
        ou o fallback automático para a CPU.
        """
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            self._device_info = f"GPU ({len(gpus)} dispositivo(s) detectado(s): {[g.name for g in gpus]})"
            logger.info("Acelerador gráfico detectado: %s", self._device_info)
        else:
            self._device_info = "CPU (Sem GPU dedicada detectada - executando via processador)"
            logger.info("Nenhuma GPU dedicada detectada. Operando em modo %s", self._device_info)

    @property
    def device_info(self) -> str:
        """Retorna informações sobre o hardware alocado para inferência."""
        return self._device_info

    def _prepare_keras_file(self, zip_filename: str) -> str:
        """
        Adapta o arquivo .zip gerado pelo Git LFS para extensão .keras esperada pelo Keras 3.

        Args:
            zip_filename: Nome do arquivo comprimido no diretório 'modelos/'.

        Returns:
            str: Caminho absoluto para o arquivo com extensão .keras em cache.
        """
        base_dir = Path(__file__).resolve().parent.parent.parent
        zip_path = base_dir / 'modelos' / zip_filename

        if not zip_path.exists():
            raise FileNotFoundError(f"Arquivo de modelo não encontrado em: {zip_path}")

        keras_filename = zip_filename.replace('.zip', '.keras')
        cached_keras_path = os.path.join(self._cache_dir, keras_filename)

        # Copia apenas se ainda não existir no diretório de cache
        if not os.path.exists(cached_keras_path):
            logger.info("Preparando arquivo .keras em cache a partir de %s", zip_filename)
            shutil.copy(str(zip_path), cached_keras_path)

        return cached_keras_path

    def get_models(self) -> Tuple[keras.Model, keras.Model]:
        """
        Recupera as instâncias em memória dos modelos de segmentação e regressão.

        Se ainda não tiverem sido carregados, realiza o carregamento com compile=False
        (otimizado exclusivamente para inferência).

        Returns:
            Tuple[keras.Model, keras.Model]: Par (modelo_segmentacao, modelo_regressao).
        """
        if self._seg_model is None or self._reg_model is None:
            with self._lock:
                if self._seg_model is None:
                    seg_path = self._prepare_keras_file('best_seg_model_y.zip')
                    logger.info("Carregando modelo UNet de segmentação...")
                    self._seg_model = keras.saving.load_model(seg_path, compile=False)
                    logger.info("Modelo de segmentação carregado com sucesso: %s", self._seg_model.name)

                if self._reg_model is None:
                    reg_path = self._prepare_keras_file('best_transfer_reg_model.zip')
                    logger.info("Carregando modelo Regressor de peso...")
                    self._reg_model = keras.saving.load_model(reg_path, compile=False)
                    logger.info("Modelo regressor carregado com sucesso: %s", self._reg_model.name)

        return self._seg_model, self._reg_model
