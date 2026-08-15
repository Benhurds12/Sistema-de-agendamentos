from django.db import models


class Local(models.Model):
    """Local onde os atendimentos serao realizados."""

    nome = models.CharField("nome", max_length=150)
    descricao = models.TextField("descricao", blank=True)
    endereco = models.CharField("endereco", max_length=255)
    ativo = models.BooleanField("ativo", default=True)

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "local"
        verbose_name_plural = "locais"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
