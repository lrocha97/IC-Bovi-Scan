"""
Modelos de dados do aplicativo core (IC-Bovi-Scan).

Define as entidades de persistência para armazenar as análises biométricas
de bovinos, imagens originais enviadas, máscaras segmentadas e resultados
estimados pelos modelos de Inteligência Artificial.
"""

import uuid
from django.db import models


class Bovine(models.Model):
    """
    Representa um bovino identificado pelo usuário através de um nome.

    Cada nova análise enviada com o mesmo nome (sem diferenciar maiúsculas de
    minúsculas) é associada ao mesmo animal, formando o histórico de pesagens.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Identificador Único (UUID)"
    )

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome",
        help_text="Nome utilizado para identificar o bovino."
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")

    class Meta:
        verbose_name = "Bovino"
        verbose_name_plural = "Bovinos"
        ordering = ['name']

    def __str__(self):
        """Retorna o nome do bovino."""
        return self.name


class BovineAnalysis(models.Model):
    """
    Representa uma análise biométrica completa de um bovino.

    Armazena a referência para a fotografia de perfil lateral enviada pelo usuário,
    a máscara de segmentação gerada pela rede UNet (EfficientNetB4), o peso estimado
    pelo regressor (EfficientNetB0), a proporção de área corporal e métricas de execução.
    """

    id = models.BigAutoField(
        primary_key=True,
        verbose_name="ID Numérico"
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Identificador Único (UUID)",
        help_text="Identificador público único utilizado para consultas via API."
    )

    bovine = models.ForeignKey(
        Bovine,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analyses',
        verbose_name="Bovino",
        help_text="Bovino identificado ao qual esta análise pertence."
    )

    original_image = models.ImageField(
        upload_to='bovines/original/%Y/%m/%d/',
        verbose_name="Imagem Original",
        help_text="Fotografia lateral do bovino submetida para inferência."
    )

    mask_image = models.ImageField(
        upload_to='bovines/masks/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="Imagem da Máscara",
        help_text="Máscara de segmentação gerada pela rede UNet delimitando a silhueta."
    )

    estimated_weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso Estimado (kg)",
        help_text="Estimativa de peso corporal em quilogramas predita pelo modelo regressor."
    )

    mask_area_percentage = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Área da Máscara (%)",
        help_text="Percentual da área corporal do bovino em relação à área total da imagem."
    )

    confidence_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Grau de Confiança (%)",
        help_text="Grau de confiança estimado para a predição."
    )

    inference_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tempo de Inferência (ms)",
        help_text="Tempo total decorrido durante a execução dos modelos de IA em milissegundos."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação",
        help_text="Data e hora em que a análise foi registrada."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização",
        help_text="Data e hora da última modificação do registro."
    )

    class Meta:
        verbose_name = "Análise Bovina"
        verbose_name_plural = "Análises Bovinas"
        ordering = ['-created_at']

    def __str__(self):
        """Retorna uma representação em texto legível da análise."""
        weight_str = f"{self.estimated_weight:.1f} kg" if self.estimated_weight is not None else "Em processamento"
        return f"Análise #{self.id} ({self.uuid}) - {weight_str}"

    @property
    def is_processed(self) -> bool:
        """
        Informa se a análise já possui os resultados processados pela IA.

        Returns:
            bool: True se tanto o peso quanto a máscara foram calculados, False caso contrário.
        """
        return self.estimated_weight is not None and bool(self.mask_image)
