"""
Processador de imagens e manipulação de máscaras biométricas.

Realiza a decodificação de imagens a partir de streams/arquivos, normalização,
redimensionamento para o tensor de entrada dos modelos (224x224), geração de
máscaras binárias, overlays visuais e codificação em Base64.
"""

import base64
import io
from typing import Any, Dict, Tuple, Union
import numpy as np
from PIL import Image


class ImageProcessor:
    """
    Conjunto de utilitários estáticos para processamento de imagens do IC-Bovi-Scan.
    """

    TARGET_SIZE: Tuple[int, int] = (224, 224)

    @staticmethod
    def load_and_preprocess(
        image_input: Union[bytes, io.BytesIO, Any]
    ) -> Tuple[np.ndarray, Image.Image]:
        """
        Carrega e pré-processa uma imagem para alimentar as redes neurais.

        Valida os dados brutos, converte para o espaço de cores RGB, redimensiona
        para 224x224 pixels e converte em um tensor NumPy com shape (1, 224, 224, 3).

        Args:
            image_input: Arquivo de imagem, stream de bytes ou arquivo de upload Django.

        Returns:
            Tuple[np.ndarray, Image.Image]:
                - Tensor com dimensões (1, 224, 224, 3) e tipo float32.
                - Imagem PIL original redimensionada para 224x224.

        Raises:
            ValueError: Se o arquivo não puder ser decodificado como uma imagem válida.
        """
        try:
            if hasattr(image_input, 'read'):
                image_bytes = image_input.read()
                if hasattr(image_input, 'seek'):
                    image_input.seek(0)
            elif isinstance(image_input, bytes):
                image_bytes = image_input
            else:
                raise ValueError("Formato de entrada de imagem não suportado.")

            pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception as exc:
            raise ValueError(f"Não foi possível processar a imagem fornecida: {exc}") from exc

        # Redimensionamento para o padrão de entrada das redes (224x224)
        resized_pil = pil_image.resize(ImageProcessor.TARGET_SIZE, Image.Resampling.BILINEAR)

        # Conversão para matriz NumPy com batch dimension (1, 224, 224, 3)
        image_array = np.array(resized_pil, dtype=np.float32)
        batch_tensor = np.expand_dims(image_array, axis=0)

        return batch_tensor, resized_pil

    @staticmethod
    def postprocess_mask(
        raw_mask_tensor: np.ndarray,
        threshold: float = 0.5
    ) -> Tuple[np.ndarray, Image.Image]:
        """
        Transforma a saída contínua do modelo UNet em uma máscara binária e imagem PNG.

        Args:
            raw_mask_tensor: Tensor de saída da UNet com shape (1, 224, 224, 1) ou (224, 224).
            threshold: Limiar de binarização (padrão 0.5).

        Returns:
            Tuple[np.ndarray, Image.Image]:
                - Matriz binária 2D NumPy (valores 0.0 ou 1.0).
                - Objeto PIL.Image em escala de cinza (valores 0 ou 255).
        """
        mask_2d = raw_mask_tensor.squeeze()
        binary_mask = (mask_2d > threshold).astype(np.float32)

        mask_uint8 = (binary_mask * 255).astype(np.uint8)
        mask_pil = Image.fromarray(mask_uint8, mode='L')

        return binary_mask, mask_pil

    @staticmethod
    def calculate_metrics(binary_mask: np.ndarray) -> Dict[str, float]:
        """
        Calcula as propriedades geométricas da silhueta corporal do bovino.

        Args:
            binary_mask: Matriz binária NumPy 2D (valores 0 e 1).

        Returns:
            Dict[str, float]: Dicionário contendo:
                - 'area_fraction': Fração da área corporal [0.0 a 1.0].
                - 'area_percentage': Percentual da área corporal [0.0% a 100.0%].
                - 'aspect_ratio': Razão largura/altura da caixa delimitadora do animal.
        """
        total_pixels = binary_mask.size
        bovine_pixels = np.sum(binary_mask)

        area_fraction = float(bovine_pixels / total_pixels) if total_pixels > 0 else 0.0
        area_percentage = area_fraction * 100.0

        # Localiza as coordenadas limites do bovino (Bounding Box)
        rows = np.any(binary_mask, axis=1)
        cols = np.any(binary_mask, axis=0)

        if np.any(rows) and np.any(cols):
            ymin, ymax = np.where(rows)[0][[0, -1]]
            xmin, xmax = np.where(cols)[0][[0, -1]]
            width = float(xmax - xmin + 1)
            height = float(ymax - ymin + 1)
            aspect_ratio = float(width / height) if height > 0 else 1.0
        else:
            aspect_ratio = 1.0

        return {
            'area_fraction': area_fraction,
            'area_percentage': round(area_percentage, 2),
            'aspect_ratio': round(aspect_ratio, 2)
        }

    @staticmethod
    def create_mask_overlay(
        original_image: Image.Image,
        binary_mask: np.ndarray,
        color_rgb: Tuple[int, int, int] = (86, 171, 47),
        alpha: float = 0.4
    ) -> Image.Image:
        """
        Desenha uma sobreposição visual semitransparente destacando a silhueta do bovino.

        Args:
            original_image: Imagem base redimensionada (PIL RGB).
            binary_mask: Matriz binária NumPy 2D.
            color_rgb: Cor do destaque (padrão verde temático #56ab2f).
            alpha: Grau de transparência da sobreposição (0.0 a 1.0).

        Returns:
            Image.Image: Imagem PIL resultante combinando foto original e máscara colorida.
        """
        base_rgb = original_image.convert('RGBA')
        overlay = Image.new('RGBA', original_image.size, (0, 0, 0, 0))

        # Cria a camada de cor na região da máscara
        color_with_alpha = (*color_rgb, int(255 * alpha))
        mask_uint8 = (binary_mask * 255).astype(np.uint8)
        mask_img = Image.fromarray(mask_uint8, mode='L')

        tint_layer = Image.new('RGBA', original_image.size, color_with_alpha)
        overlay.paste(tint_layer, (0, 0), mask=mask_img)

        # Mescla a camada de destaque sobre a imagem original
        return Image.alpha_composite(base_rgb, overlay).convert('RGB')

    @staticmethod
    def to_base64_data_uri(image: Image.Image, image_format: str = 'PNG') -> str:
        """
        Codifica uma imagem PIL em uma string Data URI Base64 pronta para exibição web.

        Args:
            image: Objeto de imagem PIL.
            image_format: Formato de codificação (padrão 'PNG').

        Returns:
            str: String no formato 'data:image/png;base64,...'
        """
        buffer = io.BytesIO()
        image.save(buffer, format=image_format)
        encoded_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/{image_format.lower()};base64,{encoded_str}"
