"""Regras de negocio da grade de horarios.

Concentradas aqui (fora da view) para que a view e os testes chamem
exatamente a mesma logica, sem duplicar regra em dois lugares.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.locais.models import Local

from .models import Atendimento, HorarioAgendamento, StatusAtendimento


@dataclass
class ResultadoGrade:
    criadas: int
    mensagem: str


def gerar_grade(
    *, local: Local, inicio: datetime, fim: datetime, duracao_minutos: int
) -> ResultadoGrade:
    """Gera a quantidade maxima de horarios completos dentro do intervalo.

    Nunca cria um slot parcial que ultrapasse `fim` (regra explicita do
    enunciado). Rejeita a geracao inteira caso o intervalo se sobreponha a
    horarios ja existentes no mesmo local.
    """
    if duracao_minutos is None or duracao_minutos <= 0:
        raise ValidationError({"duracao_minutos": ["A duracao deve ser maior que zero."]})

    if fim <= inicio:
        raise ValidationError(
            {"fim": ["A data/hora final deve ser posterior a data/hora inicial."]}
        )

    if not local.ativo:
        raise ValidationError({"local": ["Local inativo nao pode receber grades."]})

    if inicio < timezone.now():
        raise ValidationError(
            {"inicio": ["Nao e possivel gerar grade com data/hora inicial no passado."]}
        )

    duracao = timedelta(minutes=duracao_minutos)
    quantidade = int((fim - inicio) // duracao)

    if quantidade == 0:
        raise ValidationError(
            {
                "duracao_minutos": [
                    "O intervalo informado e menor que a duracao de um atendimento."
                ]
            }
        )

    fim_efetivo = inicio + duracao * quantidade

    # Sobreposicao no mesmo local: dois periodos colidem quando um comeca
    # antes do outro terminar. Comparamos contra o intervalo efetivamente
    # ocupado (fim_efetivo), nao contra o `fim` bruto informado pelo usuario.
    conflito = (
        HorarioAgendamento.objects.filter(
            local=local, inicio__lt=fim_efetivo, fim__gt=inicio
        )
        .order_by("inicio")
        .first()
    )
    if conflito is not None:
        total_conflitos = HorarioAgendamento.objects.filter(
            local=local, inicio__lt=fim_efetivo, fim__gt=inicio
        ).count()
        inicio_local = timezone.localtime(conflito.inicio)
        raise ValidationError(
            {
                "nao_campo": [
                    f"Ja existem {total_conflitos} horario(s) cadastrados neste local "
                    f"dentro do periodo informado (o primeiro conflito comeca em "
                    f"{inicio_local:%d/%m/%Y %H:%M}). Nenhuma grade foi criada."
                ]
            }
        )

    horarios = [
        HorarioAgendamento(
            local=local,
            inicio=inicio + duracao * i,
            fim=inicio + duracao * (i + 1),
            disponivel=True,
        )
        for i in range(quantidade)
    ]

    with transaction.atomic():
        HorarioAgendamento.objects.bulk_create(horarios)

    return ResultadoGrade(
        criadas=quantidade, mensagem=f"{quantidade} grades criadas com sucesso."
    )


def horarios_disponiveis_qs(local_id: int) -> "QuerySet[HorarioAgendamento]":
    """Horarios que ainda podem ser escolhidos em um novo agendamento.

    O filtro `inicio__gt=now` resolve de uma vez as duas regras do enunciado:
    datas passadas nao aparecem, e no dia corrente os horarios ja vencidos
    tambem ficam de fora — sem precisar de nenhum `if` especial para "hoje".
    """
    return HorarioAgendamento.objects.filter(
        local_id=local_id, disponivel=True, inicio__gt=timezone.now()
    ).order_by("inicio")


@transaction.atomic
def criar_atendimento(
    *, cliente, local, tipo, horario_id: int, descricao: str = "", motivo: str = ""
) -> Atendimento:
    """Reserva o horario e cria o atendimento numa unica transacao.

    O `select_for_update()` trava a linha do horario no banco ate a transacao
    terminar. Se duas requisicoes chegarem ao mesmo tempo para o mesmo
    horario, a segunda espera a primeira concluir e entao encontra
    `disponivel=False` (nao um horario "livre" desatualizado), garantindo que
    nunca dois atendimentos sejam criados para o mesmo slot.
    """
    try:
        horario = HorarioAgendamento.objects.select_for_update().get(pk=horario_id)
    except HorarioAgendamento.DoesNotExist:
        raise ValidationError({"horario": ["Horario informado nao existe."]})

    if horario.local_id != local.id:
        raise ValidationError(
            {"horario": ["O horario selecionado nao pertence ao local informado."]}
        )

    if not horario.disponivel:
        raise ValidationError(
            {"horario": ["Este horario ja esta indisponivel para agendamento."]}
        )

    if horario.inicio <= timezone.now():
        raise ValidationError({"horario": ["Nao e possivel agendar em um horario passado."]})

    if not cliente.ativo:
        raise ValidationError({"cliente": ["Cliente inativo nao pode ser agendado."]})

    if not tipo.ativo:
        raise ValidationError({"tipo": ["Tipo de atendimento inativo."]})

    atendimento = Atendimento.objects.create(
        cliente=cliente,
        local=local,
        tipo=tipo,
        horario=horario,
        data_hora=horario.inicio,
        descricao=descricao or "",
        motivo=motivo or "",
        status=StatusAtendimento.PENDENTE,
    )

    horario.disponivel = False
    horario.save(update_fields=["disponivel"])

    return atendimento


def alterar_status(
    atendimento: Atendimento, novo_status: str, *, motivo: str = "", descricao: str = ""
) -> Atendimento:
    """Aplica uma transicao de status, respeitando o fluxo permitido.

    `motivo` so e gravado ao cancelar; `descricao` so ao marcar como
    realizado — em qualquer outra transicao, esses campos sao ignorados
    mesmo que enviados (nao fazem sentido fora desses dois casos).
    """
    if novo_status == atendimento.status:
        raise ValidationError({"status": ["O atendimento ja esta neste status."]})

    if not atendimento.pode_alterar_para(novo_status):
        atual = atendimento.get_status_display()
        novo_label = StatusAtendimento(novo_status).label
        raise ValidationError(
            {
                "status": [
                    f"Transicao invalida: um atendimento com status '{atual}' nao pode "
                    f"ser alterado para '{novo_label}'."
                ]
            }
        )

    campos = ["status"]
    atendimento.status = novo_status

    if novo_status == StatusAtendimento.CANCELADO and motivo:
        atendimento.motivo = motivo
        campos.append("motivo")

    if novo_status == StatusAtendimento.REALIZADO and descricao:
        atendimento.descricao = descricao
        campos.append("descricao")

    atendimento.save(update_fields=campos)
    return atendimento
