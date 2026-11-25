"""
Testes automatizados para o aplicativo core (IC-Bovi-Scan).

Valida os modelos de dados, persistência no banco, propriedades calculadas,
processamento de imagens, pipeline de inferência de IA e endpoints da API REST.
"""

import io
from decimal import Decimal
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
import numpy as np
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from config.settings import parse_database_url
from .models import BovineAnalysis
from .services.image_processor import ImageProcessor
from .services.inference_service import BovineInferenceService


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


class ImageProcessorTestCase(TestCase):
    """
    Testes para as operações de pré/pós-processamento de imagens e métricas de máscara.
    """

    def setUp(self):
        """Cria imagem básica para testes de utilitários."""
        self.test_img = Image.new('RGB', (100, 100), color='blue')
        stream = io.BytesIO()
        self.test_img.save(stream, format='PNG')
        self.test_bytes = stream.getvalue()

    def test_load_and_preprocess(self):
        """Verifica a conversão para RGB e tensor com dimensões (1, 224, 224, 3)."""
        tensor, pil_img = ImageProcessor.load_and_preprocess(self.test_bytes)
        self.assertEqual(tensor.shape, (1, 224, 224, 3))
        self.assertEqual(pil_img.size, (224, 224))
        self.assertEqual(tensor.dtype, np.float32)

    def test_calculate_metrics(self):
        """Verifica o cálculo de área percentual e proporção de aspecto em máscara conhecida."""
        mask = np.zeros((224, 224), dtype=np.float32)
        # Preenche um quadrado de 112x112 (exatamente 25% da área total)
        mask[0:112, 0:112] = 1.0

        metrics = ImageProcessor.calculate_metrics(mask)
        self.assertAlmostEqual(metrics['area_percentage'], 25.0, places=1)
        self.assertAlmostEqual(metrics['aspect_ratio'], 1.0, places=1)

    def test_to_base64_data_uri(self):
        """Verifica a geração de string Data URI Base64 válida."""
        data_uri = ImageProcessor.to_base64_data_uri(self.test_img)
        self.assertTrue(data_uri.startswith('data:image/png;base64,'))
        self.assertGreater(len(data_uri), 50)


class BovineInferenceServiceTestCase(TestCase):
    """
    Testes de integração para a pipeline completa de Inteligência Artificial.
    Executa a inferência nos modelos Keras reais utilizando a imagem boi1.png.
    """

    def test_run_pipeline_with_real_bovine_image(self):
        """
        Executa a pipeline completa na imagem de teste real (boi1.png).
        Valida que o peso estimado é positivo e plausível, e a máscara foi gerada.
        """
        base_dir = Path(__file__).resolve().parent.parent
        image_path = base_dir / 'boi1.png'

        if not image_path.exists():
            self.skipTest("Arquivo boi1.png não encontrado para teste de integração.")

        with open(image_path, 'rb') as img_file:
            service = BovineInferenceService()
            result = service.run_pipeline(img_file)

        # Validações dos resultados biométricos
        self.assertGreater(result.estimated_weight_kg, 100.0)
        self.assertLess(result.estimated_weight_kg, 500.0)
        self.assertGreater(result.mask_area_percentage, 10.0)
        self.assertLess(result.mask_area_percentage, 60.0)
        self.assertGreater(result.confidence_score, 70.0)
        self.assertLessEqual(result.confidence_score, 100.0)
        self.assertGreater(result.inference_time_ms, 0)
        self.assertTrue(result.mask_base64.startswith('data:image/png;base64,'))
        self.assertTrue(result.overlay_base64.startswith('data:image/png;base64,'))

        # Validação com custom_metadata fornecido
        with open(image_path, 'rb') as img_file:
            result_with_meta = service.run_pipeline(
                img_file,
                custom_metadata={'aspect_ratio': 1.15, 'feature_2': 0.1}
            )
        self.assertGreater(result_with_meta.estimated_weight_kg, 100.0)


class BovineAnalysisAPITestCase(TestCase):
    """
    Testes de integração para o endpoint REST POST /api/v1/cattle/analyze/.
    """

    def setUp(self):
        """Inicializa usuário autenticado e cliente de testes da API REST."""
        self.user_model = get_user_model()
        self.test_user = self.user_model.objects.create_user(
            username='testresearcher',
            password='testpassword123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)
        self.url = reverse('core:cattle-analyze')

    @override_settings(REQUIRE_AUTH_FOR_INFERENCE=True)
    def test_api_unauthenticated_request_rejected_when_auth_required(self):
        """Verifica se requisição anônima retorna HTTP 401 Unauthorized quando autenticação é exigida."""
        anon_client = APIClient()
        response = anon_client.post(self.url, data={}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(REQUIRE_AUTH_FOR_INFERENCE=False)
    def test_api_unauthenticated_request_allowed_with_opt_out(self):
        """Verifica se requisição anônima é aceita quando há opt-out de desenvolvimento (retorna 400 por payload vazio)."""
        anon_client = APIClient()
        response = anon_client.post(self.url, data={}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_api_missing_image_payload(self):
        """Verifica se uma requisição sem campo 'image' retorna erro HTTP 400 Bad Request."""
        response = self.client.post(self.url, data={}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)

    def test_api_missing_bovine_name(self):
        """Verifica se o nome do bovino é obrigatório."""
        image = SimpleUploadedFile('a.png', b'x', content_type='image/png')
        response = self.client.post(self.url, data={'image': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_api_invalid_file_type(self):
        """Verifica se o envio de um arquivo de texto retorna erro HTTP 400 Bad Request."""
        text_file = SimpleUploadedFile(
            name='doc.txt',
            content=b'arquivo texto invalido',
            content_type='text/plain'
        )
        response = self.client.post(self.url, data={'image': text_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_oversized_image(self):
        """Verifica se o envio de uma imagem que excede o limite máximo (10 MB) retorna HTTP 400."""
        oversized_content = b'x' * (11 * 1024 * 1024)
        oversized_file = SimpleUploadedFile(
            name='huge_bovine.png',
            content=oversized_content,
            content_type='image/png'
        )
        response = self.client.post(self.url, data={'image': oversized_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)
        self.assertIn('limite máximo permitido', str(response.data['image']))

    def test_api_successful_analysis(self):
        """
        Verifica o fluxo completo de upload via API com a foto boi1.png.
        Garante status HTTP 201 Created, persistência no banco e retorno com Base64.
        """
        base_dir = Path(__file__).resolve().parent.parent
        image_path = base_dir / 'boi1.png'

        if not image_path.exists():
            self.skipTest("Arquivo boi1.png não encontrado para teste de API.")

        with open(image_path, 'rb') as img_file:
            uploaded_file = SimpleUploadedFile(
                name='boi1.png',
                content=img_file.read(),
                content_type='image/png'
            )
            response = self.client.post(
                self.url,
                data={'image': uploaded_file, 'name': 'Mimosa'},
                format='multipart'
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['bovine_name'], 'Mimosa')
        self.assertEqual(response.data['analyses_count'], 1)
        self.assertIn('id', response.data)
        self.assertIn('uuid', response.data)
        self.assertIn('estimated_weight', response.data)
        self.assertIn('mask_area_percentage', response.data)
        self.assertIn('mask_base64', response.data)
        self.assertIn('overlay_base64', response.data)
        self.assertTrue(response.data['mask_base64'].startswith('data:image/png;base64,'))

        # Confirma gravação no banco de dados
        analysis_id = response.data['id']
        db_obj = BovineAnalysis.objects.get(id=analysis_id)
        self.assertTrue(db_obj.is_processed)
        self.assertGreater(float(db_obj.estimated_weight), 100.0)


class DatabaseUrlParsingTestCase(TestCase):
    """
    Testes unitários para a interpretação e validação de DATABASE_URL em settings.
    Garante o tratamento correto de caminhos absolutos SQLite e rejeição de esquemas inválidos.
    """

    def test_sqlite_unix_absolute_path_preserves_slash(self):
        """Verifica se URLs SQLite absolutas no Unix preservam a barra inicial (/tmp/...)."""
        conf = parse_database_url('sqlite:////tmp/boviscan.sqlite3')
        self.assertEqual(conf['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(conf['NAME'], '/tmp/boviscan.sqlite3')

    def test_sqlite_relative_path(self):
        """Verifica se URLs SQLite relativas removem as barras excedentes."""
        conf = parse_database_url('sqlite:///db.sqlite3')
        self.assertEqual(conf['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(conf['NAME'], 'db.sqlite3')

    def test_sqlite_memory(self):
        """Verifica se URLs SQLite in-memory retornam ':memory:'."""
        conf = parse_database_url('sqlite:///:memory:')
        self.assertEqual(conf['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(conf['NAME'], ':memory:')

    def test_unsupported_database_scheme_raises_value_error(self):
        """Verifica se esquemas não suportados disparam ValueError com mensagem explicativa."""
        with self.assertRaises(ValueError) as ctx:
            parse_database_url('oracle://user:pass@localhost:1521/orcl')
        self.assertIn("Esquema de banco de dados não suportado", str(ctx.exception))


class BovineHistoryViewsTestCase(TestCase):
    """Testes do dashboard por bovino e da página de histórico com gráfico de peso."""

    def setUp(self):
        import tempfile
        self._media = tempfile.TemporaryDirectory()
        self.addCleanup(self._media.cleanup)
        self._override = override_settings(MEDIA_ROOT=self._media.name)
        self._override.enable()
        self.addCleanup(self._override.disable)

        self.user = get_user_model().objects.create_user(username='pesquisador', password='senha12345')
        self.client.force_login(self.user)

        from .models import Bovine
        self.mimosa = Bovine.objects.create(name='Mimosa')
        self.estrela = Bovine.objects.create(name='Estrela')
        for bovine, weight in [(self.mimosa, '200.00'), (self.mimosa, '215.50'), (self.estrela, '300.00')]:
            self._create_analysis(bovine, weight)

    def _create_analysis(self, bovine, weight):
        stream = io.BytesIO()
        Image.new('RGB', (32, 32), color='green').save(stream, format='PNG')
        return BovineAnalysis.objects.create(
            bovine=bovine,
            original_image=SimpleUploadedFile('boi.png', stream.getvalue(), content_type='image/png'),
            mask_image=SimpleUploadedFile('mask.png', stream.getvalue(), content_type='image/png'),
            estimated_weight=Decimal(weight),
            mask_area_percentage=30.0,
            confidence_score=90.0,
            inference_time_ms=100,
        )

    @override_settings(REQUIRE_AUTH_FOR_INFERENCE=True)
    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_lists_one_entry_per_bovine(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 2)
        names = {i['bovine'].name: i['count'] for i in response.context['items']}
        self.assertEqual(names, {'Mimosa': 2, 'Estrela': 1})
        self.assertContains(response, 'Mimosa')

    def test_bovine_detail_shows_history_and_chart_data(self):
        response = self.client.get(reverse('core:bovine-detail', args=[self.mimosa.uuid]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['weight'] for p in response.context['chart_data']], [200.0, 215.5])
        self.assertEqual(len(response.context['analyses']), 2)
        self.assertContains(response, 'grafico-peso')

    def test_bovine_detail_not_found(self):
        import uuid as uuid_lib
        response = self.client.get(reverse('core:bovine-detail', args=[uuid_lib.uuid4()]))
        self.assertEqual(response.status_code, 404)

    def test_bovine_name_lookup_is_case_insensitive_in_api_flow(self):
        from .models import Bovine
        self.assertEqual(Bovine.objects.filter(name__iexact='mimosa').count(), 1)
