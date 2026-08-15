from django.db import models

from .validators import somente_digitos, validar_documento


class Cliente(models.Model):
    """Pessoa que sera agendada para receber o servico."""

    nome = models.CharField("nome", max_length=150)
    documento = models.CharField(
        "documento", max_length=14, unique=True, validators=[validar_documento]
    )
    telefone = models.CharField("telefone", max_length=20)
    email = models.EmailField("e-mail", max_length=254)
    ativo = models.BooleanField("ativo", default=True)

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        # Documento e sempre persistido so com digitos, garantindo que a
        # unicidade valha mesmo se alguem digitar com ou sem mascara.
        self.documento = somente_digitos(self.documento)
        return super().save(*args, **kwargs)
