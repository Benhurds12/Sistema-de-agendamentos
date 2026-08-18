from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.agendamentos.models import HorarioAgendamento
from apps.locais.models import Local


@pytest.fixture
def local() -> Local:
    return Local.objects.create(nome="Unidade Central", endereco="Rua A, 1")


def _amanha_as(hora: int, minuto: int = 0):
    """Horario no dia seguinte, evitando testes quebrarem por causa da hora atual."""
    base = timezone.localtime() + timedelta(days=1)
    return base.replace(hour=hora, minute=minuto, second=0, microsecond=0)


@pytest.mark.django_db
def test_gera_quantidade_maxima_de_slots_completos(api_client, local):
    inicio = _amanha_as(8, 0)
    fim = _amanha_as(12, 0)  # 4h / 30min = 8 slots exatos

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 30,
        },
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["criadas"] == 8
    assert resposta.data["mensagem"] == "8 grades criadas com sucesso."
    assert HorarioAgendamento.objects.filter(local=local).count() == 8


@pytest.mark.django_db
def test_nao_gera_slot_parcial_que_ultrapasse_o_fim(api_client, local):
    inicio = _amanha_as(8, 0)
    fim = _amanha_as(9, 10)  # 1h10min / 30min = 2 slots completos, 10min descartados

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 30,
        },
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["criadas"] == 2
    ultimo = HorarioAgendamento.objects.filter(local=local).order_by("-fim").first()
    assert ultimo.fim == inicio + timedelta(hours=1)  # 09:00, nao 09:10


@pytest.mark.django_db
def test_fim_anterior_ao_inicio_retorna_400(api_client, local):
    inicio = _amanha_as(10, 0)
    fim = _amanha_as(9, 0)

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 30,
        },
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_duracao_zero_retorna_400(api_client, local):
    inicio = _amanha_as(8, 0)
    fim = _amanha_as(12, 0)

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 0,
        },
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_intervalo_menor_que_duracao_retorna_400(api_client, local):
    inicio = _amanha_as(8, 0)
    fim = _amanha_as(8, 20)  # 20min de intervalo, duracao de 30min: 0 slots

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 30,
        },
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert HorarioAgendamento.objects.count() == 0


@pytest.mark.django_db
def test_grade_sobreposta_no_mesmo_local_retorna_400(api_client, local):
    inicio = _amanha_as(8, 0)
    fim = _amanha_as(10, 0)
    payload = {
        "local": local.id,
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "duracao_minutos": 30,
    }

    primeira = api_client.post("/api/horarios/gerar-grade/", payload)
    assert primeira.status_code == status.HTTP_201_CREATED

    segunda = api_client.post("/api/horarios/gerar-grade/", payload)

    assert segunda.status_code == status.HTTP_400_BAD_REQUEST
    # Nenhuma grade nova foi criada; continuam sendo so as 4 da primeira geracao.
    assert HorarioAgendamento.objects.filter(local=local).count() == 4


@pytest.mark.django_db
def test_mesmo_intervalo_em_outro_local_e_permitido(api_client, local):
    outro_local = Local.objects.create(nome="Unidade Sul", endereco="Rua B, 2")
    inicio = _amanha_as(8, 0)
    fim = _amanha_as(10, 0)
    payload_base = {"inicio": inicio.isoformat(), "fim": fim.isoformat(), "duracao_minutos": 30}

    primeira = api_client.post(
        "/api/horarios/gerar-grade/", {**payload_base, "local": local.id}
    )
    segunda = api_client.post(
        "/api/horarios/gerar-grade/", {**payload_base, "local": outro_local.id}
    )

    assert primeira.status_code == status.HTTP_201_CREATED
    assert segunda.status_code == status.HTTP_201_CREATED
    assert HorarioAgendamento.objects.count() == 8


@pytest.mark.django_db
def test_inicio_no_passado_retorna_400(api_client, local):
    inicio = timezone.now() - timedelta(hours=1)
    fim = timezone.now() + timedelta(hours=1)

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 30,
        },
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
