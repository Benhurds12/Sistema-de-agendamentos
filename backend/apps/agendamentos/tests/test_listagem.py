from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.test import APIClient

from apps.agendamentos.models import Atendimento, HorarioAgendamento, StatusAtendimento
from apps.clientes.models import Cliente
from apps.locais.models import Local
from apps.tipos_atendimento.models import TipoAtendimento


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def _criar_atendimento(nome_cliente, local, tipo, status_=StatusAtendimento.PENDENTE):
    documentos = {
        "Ana": "11144477735",
        "Bruno": "52998224725",
        "Carla": "12345678909",
    }
    cliente = Cliente.objects.create(
        nome=nome_cliente,
        documento=documentos.get(nome_cliente, "11144477735"),
        telefone="11999998888",
        email=f"{nome_cliente.lower()}@example.com",
    )
    inicio = timezone.now() + timedelta(days=1)
    horario = HorarioAgendamento.objects.create(
        local=local, inicio=inicio, fim=inicio + timedelta(minutes=30), disponivel=False
    )
    return Atendimento.objects.create(
        cliente=cliente, local=local, tipo=tipo, horario=horario, data_hora=inicio,
        status=status_,
    )


@pytest.fixture
def cenario():
    """2 locais, 1 tipo, 3 atendimentos com status e clientes diferentes."""
    local_a = Local.objects.create(nome="Unidade A", endereco="Rua A, 1")
    local_b = Local.objects.create(nome="Unidade B", endereco="Rua B, 2")
    tipo = TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)

    a1 = _criar_atendimento("Ana", local_a, tipo, StatusAtendimento.PENDENTE)
    a2 = _criar_atendimento("Bruno", local_a, tipo, StatusAtendimento.REALIZADO)
    a3 = _criar_atendimento("Carla", local_b, tipo, StatusAtendimento.CANCELADO)

    return {"local_a": local_a, "local_b": local_b, "atendimentos": [a1, a2, a3]}


@pytest.mark.django_db
def test_listar_sem_filtro_retorna_todos(api_client, cenario):
    resposta = api_client.get("/api/atendimentos/")

    assert resposta.status_code == http_status.HTTP_200_OK
    assert len(resposta.data) == 3


@pytest.mark.django_db
def test_filtrar_por_status(api_client, cenario):
    resposta = api_client.get("/api/atendimentos/?status=PENDENTE")

    assert resposta.status_code == http_status.HTTP_200_OK
    assert len(resposta.data) == 1
    assert resposta.data[0]["status"] == "PENDENTE"


@pytest.mark.django_db
def test_filtrar_por_local(api_client, cenario):
    resposta = api_client.get(f"/api/atendimentos/?local={cenario['local_a'].id}")

    assert resposta.status_code == http_status.HTTP_200_OK
    assert len(resposta.data) == 2


@pytest.mark.django_db
def test_filtrar_por_nome_de_cliente_parcial(api_client, cenario):
    resposta = api_client.get("/api/atendimentos/?cliente_nome=ana")

    assert resposta.status_code == http_status.HTTP_200_OK
    assert len(resposta.data) == 1
    assert resposta.data[0]["cliente_nome"] == "Ana"


@pytest.mark.django_db
def test_filtros_combinados(api_client, cenario):
    resposta = api_client.get(
        f"/api/atendimentos/?local={cenario['local_a'].id}&status=REALIZADO"
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    assert len(resposta.data) == 1
    assert resposta.data[0]["cliente_nome"] == "Bruno"


@pytest.mark.django_db
def test_indicadores_sem_filtro(api_client, cenario):
    resposta = api_client.get("/api/atendimentos/indicadores/")

    assert resposta.status_code == http_status.HTTP_200_OK
    assert resposta.data == {
        "total": 3,
        "pendentes": 1,
        "realizados": 1,
        "cancelados": 1,
        "nao_compareceram": 0,
    }


@pytest.mark.django_db
def test_indicadores_acompanham_os_filtros_aplicados(api_client, cenario):
    resposta = api_client.get(f"/api/atendimentos/indicadores/?local={cenario['local_a'].id}")

    assert resposta.status_code == http_status.HTTP_200_OK
    assert resposta.data["total"] == 2
    assert resposta.data["pendentes"] == 1
    assert resposta.data["realizados"] == 1
    assert resposta.data["cancelados"] == 0
