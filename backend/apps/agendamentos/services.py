"""Regras de negocio da grade de horarios.

Concentradas aqui (fora da view) para que a view e os testes chamem
exatamente a mesma logica, sem duplicar regra em dois lugares.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.locais.models import Local

from .models import HorarioAgendamento


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
