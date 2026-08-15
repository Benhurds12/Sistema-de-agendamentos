from django.core.validators import MinValueValidator
from django.db import models


class TipoAtendimento(models.Model):
    """Tipo de servico que podera ser agendado."""

    nome = models.CharField("nome", max_length=150)
    descricao = models.TextField("descricao", blank=True)
    duracao_minutos = models.PositiveIntegerField(
        "duracao (minutos)", validators=[MinValueValidator(1)]
    )
    ativo = models.BooleanField("ativo", default=True)

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "tipo de atendimento"
        verbose_name_plural = "tipos de atendimento"
        ordering = ["nome"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duracao_minutos__gt=0),
                name="ck_tipo_duracao_positiva",
            )
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.duracao_minutos} min)"
