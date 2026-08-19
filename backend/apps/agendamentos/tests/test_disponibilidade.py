from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.agendamentos.models import HorarioAgendamento
from apps.locais.models import Local


@pytest.fixture
def local() -> Local:
    return Local.objects.create(nome="Unidade Central", endereco="Rua A, 1")


def _criar_horario(local, inicio, disponivel=True):
    return HorarioAgendamento.objects.create(
        local=local, inicio=inicio, fim=inicio + timedelta(minutes=30), disponivel=disponivel
    )


@pytest.mark.django_db
def test_datas_disponiveis_ignora_horarios_passados(api_client, local):
    agora = timezone.now()
    _criar_horario(local, agora - timedelta(hours=1))  # passado: nao deve aparecer
    _criar_horario(local, agora + timedelta(days=1))  # futuro: deve aparecer

    resposta = api_client.get(f"/api/horarios/datas-disponiveis/?local={local.id}")

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 1
    assert resposta.data[0]["total_horarios"] == 1


@pytest.mark.django_db
def test_datas_disponiveis_ignora_horarios_ja_usados(api_client, local):
    agora = timezone.now()
    _criar_horario(local, agora + timedelta(days=1), disponivel=False)  # ja agendado

    resposta = api_client.get(f"/api/horarios/datas-disponiveis/?local={local.id}")

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 0


@pytest.mark.django_db
def test_datas_disponiveis_sem_local_retorna_400(api_client):
    resposta = api_client.get("/api/horarios/datas-disponiveis/")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_horarios_disponiveis_de_uma_data_especifica(api_client, local):
    dia = timezone.localtime() + timedelta(days=1)
    manha = dia.replace(hour=9, minute=0, second=0, microsecond=0)
    tarde = dia.replace(hour=15, minute=0, second=0, microsecond=0)
    outro_dia = dia + timedelta(days=1)

    _criar_horario(local, manha)
    _criar_horario(local, tarde)
    _criar_horario(local, outro_dia)

    resposta = api_client.get(
        f"/api/horarios/horarios-disponiveis/?local={local.id}&data={dia.date().isoformat()}"
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 2


@pytest.mark.django_db
def test_horarios_disponiveis_hoje_esconde_horarios_ja_passados(api_client, local):
    """Regra explicita do PDF: no dia atual, horarios ja vencidos ficam de fora."""
    agora = timezone.localtime()
    ja_passou = agora - timedelta(minutes=30)
    ainda_vai_acontecer = agora + timedelta(hours=2)

    _criar_horario(local, ja_passou)
    _criar_horario(local, ainda_vai_acontecer)

    resposta = api_client.get(
        f"/api/horarios/horarios-disponiveis/?local={local.id}&data={agora.date().isoformat()}"
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 1


@pytest.mark.django_db
def test_horarios_disponiveis_sem_parametros_retorna_400(api_client, local):
    resposta = api_client.get(f"/api/horarios/horarios-disponiveis/?local={local.id}")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_listagem_generica_de_horarios_filtra_por_local(api_client, local):
    """Regressao: o ?local= da listagem generica (GET /api/horarios/) precisa
    filtrar de verdade, e nao devolver horarios de outros locais."""
    outro_local = Local.objects.create(nome="Unidade Sul", endereco="Rua B, 2")
    agora = timezone.now()
    _criar_horario(local, agora + timedelta(days=1))
    _criar_horario(outro_local, agora + timedelta(days=1))

    resposta = api_client.get(f"/api/horarios/?local={local.id}")

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 1
    assert resposta.data[0]["local"] == local.id
