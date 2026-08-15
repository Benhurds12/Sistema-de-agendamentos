import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.tipos_atendimento.models import TipoAtendimento


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_criar_tipo_atendimento_com_dados_validos(api_client):
    payload = {
        "nome": "Consulta de rotina",
        "descricao": "Atendimento padrao",
        "duracao_minutos": 30,
    }

    resposta = api_client.post("/api/tipos-atendimento/", payload)

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["ativo"] is True
    assert TipoAtendimento.objects.count() == 1


@pytest.mark.django_db
def test_criar_tipo_atendimento_com_duracao_zero_retorna_400(api_client):
    payload = {"nome": "Consulta de rotina", "duracao_minutos": 0}

    resposta = api_client.post("/api/tipos-atendimento/", payload)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "duracao_minutos" in resposta.data
    assert TipoAtendimento.objects.count() == 0


@pytest.mark.django_db
def test_criar_tipo_atendimento_com_duracao_negativa_retorna_400(api_client):
    payload = {"nome": "Consulta de rotina", "duracao_minutos": -10}

    resposta = api_client.post("/api/tipos-atendimento/", payload)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "duracao_minutos" in resposta.data


@pytest.mark.django_db
def test_listar_tipos_atendimento(api_client):
    TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)
    TipoAtendimento.objects.create(nome="Retorno", duracao_minutos=15)

    resposta = api_client.get("/api/tipos-atendimento/")

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 2


@pytest.mark.django_db
def test_desativar_tipo_atendimento_via_patch(api_client):
    tipo = TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)

    resposta = api_client.patch(f"/api/tipos-atendimento/{tipo.id}/", {"ativo": False})

    assert resposta.status_code == status.HTTP_200_OK
    tipo.refresh_from_db()
    assert tipo.ativo is False
