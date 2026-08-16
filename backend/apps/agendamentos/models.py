from django.db import models
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.locais.models import Local
from apps.tipos_atendimento.models import TipoAtendimento


class StatusAtendimento(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    CANCELADO = "CANCELADO", "Cancelado"
    NAO_COMPARECEU = "NAO_COMPARECEU", "Nao compareceu"
    REALIZADO = "REALIZADO", "Realizado"


#: Transicoes permitidas. Todo atendimento nasce PENDENTE e, uma vez em um
#: status final, nao pode mais ser alterado.
TRANSICOES_PERMITIDAS: dict[str, set[str]] = {
    StatusAtendimento.PENDENTE: {
        StatusAtendimento.REALIZADO,
        StatusAtendimento.CANCELADO,
        StatusAtendimento.NAO_COMPARECEU,
    },
    StatusAtendimento.REALIZADO: set(),
    StatusAtendimento.CANCELADO: set(),
    StatusAtendimento.NAO_COMPARECEU: set(),
}


class HorarioAgendamento(models.Model):
    """Um slot da grade de atendimento, vinculado a um local."""

    local = models.ForeignKey(
        Local, on_delete=models.PROTECT, related_name="horarios", verbose_name="local"
    )
    inicio = models.DateTimeField("inicio", db_index=True)
    fim = models.DateTimeField("fim")
    disponivel = models.BooleanField("disponivel", default=True, db_index=True)

    class Meta:
        verbose_name = "horario de agendamento"
        verbose_name_plural = "horarios de agendamento"
        ordering = ["inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["local", "inicio"], name="uniq_horario_local_inicio"
            ),
            models.CheckConstraint(
                condition=models.Q(fim__gt=models.F("inicio")),
                name="ck_horario_fim_maior_inicio",
            ),
        ]
        indexes = [models.Index(fields=["local", "disponivel", "inicio"])]

    def __str__(self) -> str:
        return f"{self.local} - {self.inicio:%d/%m/%Y %H:%M}"

    @property
    def passado(self) -> bool:
        return self.inicio <= timezone.now()


class Atendimento(models.Model):
    """Servico agendado para um cliente em um horario da grade.

    Cancelar um atendimento NAO libera o horario para reagendamento (decisao
    de negocio: o PDF nao especifica esse comportamento, e a leitura literal
    do texto e que o horario fica indisponivel permanentemente apos o uso).
    """

    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="atendimentos"
    )
    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name="atendimentos")
    tipo = models.ForeignKey(
        TipoAtendimento,
        on_delete=models.PROTECT,
        related_name="atendimentos",
        verbose_name="tipo de atendimento",
    )
    horario = models.OneToOneField(
        HorarioAgendamento,
        on_delete=models.PROTECT,
        related_name="atendimento",
        verbose_name="horario da grade",
    )
    data_hora = models.DateTimeField("data e hora do atendimento", db_index=True)
    motivo = models.TextField("motivo", blank=True)
    descricao = models.TextField("descricao", blank=True)
    status = models.CharField(
        "status",
        max_length=20,
        choices=StatusAtendimento.choices,
        default=StatusAtendimento.PENDENTE,
        db_index=True,
    )

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "atendimento"
        verbose_name_plural = "atendimentos"
        ordering = ["-data_hora"]

    def __str__(self) -> str:
        return f"{self.cliente} - {self.data_hora:%d/%m/%Y %H:%M} ({self.get_status_display()})"

    def pode_alterar_para(self, novo_status: str) -> bool:
        return novo_status in TRANSICOES_PERMITIDAS.get(self.status, set())
