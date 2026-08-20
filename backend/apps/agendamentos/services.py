"""Regras de negocio da grade de horarios.

Concentradas aqui (fora da view) para que a view e os testes chamem
exatamente a mesma logica, sem duplicar regra em dois lugares.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.locais.models import Local

from .models import Atendimento, HorarioAgendamento, StatusAtendimento


@dataclass
class ResultadoGrade:
    criadas: int
    mensagem: str


#: Valores de `date.weekday()` para sabado (5) e domingo (6).
_FIM_DE_SEMANA = {5, 6}


def _janelas_diarias(
    inicio: datetime, fim: datetime, *, apenas_dias_uteis: bool = False
) -> list[tuple[datetime, datetime]]:
    """Uma janela [inicio_do_dia, fim_do_dia) por dia do intervalo.

    O horario (nao a data) de `inicio` e `fim` define o expediente diario,
    repetido em todos os dias do intervalo. Ex.: inicio dia 17 as 08:00 e fim
    dia 21 as 18:00 gera 5 janelas (17 a 21), cada uma das 08:00 as 18:00 —
    nenhum horario cai na madrugada entre um dia e o proximo.

    Se `apenas_dias_uteis=True`, sabados e domingos sao pulados por completo
    (nenhuma janela e gerada para eles).
    """
    hora_inicio_diaria = inicio.timetz()
    hora_fim_diaria = fim.timetz()

    if hora_fim_diaria <= hora_inicio_diaria:
        raise ValidationError(
            {
                "fim": [
                    "O horario de fim deve ser posterior ao horario de inicio "
                    "em cada dia (ex.: inicio as 08:00 e fim as 18:00)."
                ]
            }
        )

    janelas = []
    dia_atual = inicio.date()
    while dia_atual <= fim.date():
        if not (apenas_dias_uteis and dia_atual.weekday() in _FIM_DE_SEMANA):
            janela_inicio = datetime.combine(dia_atual, hora_inicio_diaria)
            janela_fim = datetime.combine(dia_atual, hora_fim_diaria)
            janelas.append((janela_inicio, janela_fim))
        dia_atual += timedelta(days=1)

    if apenas_dias_uteis and not janelas:
        raise ValidationError(
            {
                "apenas_dias_uteis": [
                    "O intervalo informado nao contem nenhum dia util "
                    "(sabado/domingo foram excluidos)."
                ]
            }
        )

    return janelas


def gerar_grade(
    *,
    local: Local,
    inicio: datetime,
    fim: datetime,
    duracao_minutos: int,
    apenas_dias_uteis: bool = False,
) -> ResultadoGrade:
    """Gera a quantidade maxima de horarios completos dentro do intervalo.

    O intervalo pode abranger varios dias; nesse caso, cada dia respeita a
    mesma janela diaria definida pelo horario de `inicio`/`fim` (ex.: sempre
    das 08:00 as 18:00) — nunca gera horario fora desse expediente, mesmo
    que o intervalo bruto atravesse a madrugada.

    Nunca cria um slot parcial que ultrapasse o fim de cada janela (regra
    explicita do enunciado). Rejeita a geracao inteira caso qualquer janela
    se sobreponha a horarios ja existentes no mesmo local.
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
    janelas = _janelas_diarias(inicio, fim, apenas_dias_uteis=apenas_dias_uteis)

    horarios = []
    for janela_inicio, janela_fim in janelas:
        cursor = janela_inicio
        while cursor + duracao <= janela_fim:
            horarios.append(
                HorarioAgendamento(
                    local=local, inicio=cursor, fim=cursor + duracao, disponivel=True
                )
            )
            cursor += duracao

    if not horarios:
        raise ValidationError(
            {
                "duracao_minutos": [
                    "O intervalo informado e menor que a duracao de um atendimento."
                ]
            }
        )

    # Sobreposicao no mesmo local: comparamos contra cada janela DIARIA (nao
    # contra cada slot individual) — e equivalente, ja que os slots preenchem
    # a janela sem buracos, e evita checar dezenas de sub-intervalos a toa.
    # Isso tambem evita falso-positivo: um horario existente as 22h (fora do
    # expediente) nao deveria bloquear uma nova grade das 08h as 18h.
    condicoes_sobreposicao = Q()
    for janela_inicio, janela_fim in janelas:
        condicoes_sobreposicao |= Q(inicio__lt=janela_fim, fim__gt=janela_inicio)

    conflitos_qs = HorarioAgendamento.objects.filter(local=local).filter(
        condicoes_sobreposicao
    )
    conflito = conflitos_qs.order_by("inicio").first()
    if conflito is not None:
        total_conflitos = conflitos_qs.count()
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

    quantidade = len(horarios)

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
