import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.locais.models import Local


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_criar_local_com_dados_validos(api_client):
    payload = {
        "nome": "Clinica Central",
        "descricao": "Unidade principal",
        "endereco": "Rua das Flores, 123",
    }

    resposta = api_client.post("/api/locais/", payload)

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["ativo"] is True
    assert Local.objects.count() == 1


@pytest.mark.django_db
def test_criar_local_sem_endereco_retorna_400(api_client):
    payload = {"nome": "Clinica Central", "endereco": ""}

    resposta = api_client.post("/api/locais/", payload)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "endereco" in resposta.data
    assert Local.objects.count() == 0


@pytest.mark.django_db
def test_listar_locais(api_client):
    Local.objects.create(nome="Unidade A", endereco="Rua A, 1")
    Local.objects.create(nome="Unidade B", endereco="Rua B, 2")

    resposta = api_client.get("/api/locais/")

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 2


@pytest.mark.django_db
def test_desativar_local_via_patch(api_client):
    local = Local.objects.create(nome="Unidade A", endereco="Rua A, 1")

    resposta = api_client.patch(f"/api/locais/{local.id}/", {"ativo": False})

    assert resposta.status_code == status.HTTP_200_OK
    local.refresh_from_db()
    assert local.ativo is False
