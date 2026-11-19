"""
Testes automatizados para o aplicativo core (IC-Bovi-Scan).

Valida os modelos de dados, persistência no banco, propriedades calculadas
e integridade dos campos da entidade BovineAnalysis.
"""

import io
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from .models import BovineAnalysis


class BovineAnalysisModelTestCase(TestCase):
    """
    Conjunto de testes unitários para a entidade BovineAnalysis.
    Verifica a persistência, integridade de dados e métodos auxiliares.
    """

    def setUp(self):
        """Cria uma imagem de teste em memória (formato PNG 224x224)."""
        image_stream = io.BytesIO()
        test_image = Image.new('RGB', (224, 224), color='green')
        test_image.save(image_stream, format='PNG')
        image_stream.seek(0)

        self.mock_image = SimpleUploadedFile(
            name='test_bovine.png',
            content=image_stream.read(),
            content_type='image/png'
        )

    def test_create_bovine_analysis_initial_state(self):
        """
        Testa a criação de um registro inicial de análise.
        Verifica se os campos padrão são preenchidos e o status de processamento é falso.
        """
        analysis = BovineAnalysis.objects.create(
            original_image=self.mock_image
        )

        self.assertIsNotNone(analysis.id)
        self.assertIsNotNone(analysis.uuid)
        self.assertIn('test_bovine', analysis.original_image.name)
        self.assertIsNone(analysis.mask_image.name)
        self.assertIsNone(analysis.estimated_weight)
        self.assertFalse(analysis.is_processed)
        self.assertIn("Em processamento", str(analysis))

    def test_bovine_analysis_processed_state(self):
        """
        Testa a atualização dos dados após o processamento pela IA.
        Verifica a precisão decimal do peso, percentual de área e tempo de inferência.
        """
        mask_stream = io.BytesIO()
        mask_img = Image.new('L', (224, 224), color=255)
        mask_img.save(mask_stream, format='PNG')
        mask_stream.seek(0)

        mock_mask = SimpleUploadedFile(
            name='test_mask.png',
            content=mask_stream.read(),
            content_type='image/png'
        )

        analysis = BovineAnalysis.objects.create(
            original_image=self.mock_image,
            mask_image=mock_mask,
            estimated_weight=Decimal('226.50'),
            mask_area_percentage=26.35,
            confidence_score=94.5,
            inference_time_ms=320
        )

        self.assertTrue(analysis.is_processed)
        self.assertEqual(analysis.estimated_weight, Decimal('226.50'))
        self.assertEqual(analysis.mask_area_percentage, 26.35)
        self.assertEqual(analysis.inference_time_ms, 320)
        self.assertIn("226.5 kg", str(analysis))
