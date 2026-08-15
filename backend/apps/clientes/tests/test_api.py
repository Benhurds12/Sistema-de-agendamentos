import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.clientes.models import Cliente

CPF_VALIDO_1 = "111.444.777-35"
CPF_VALIDO_2 = "529.982.247-25"
CPF_INVALIDO = "111.111.111-11"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_criar_cliente_com_dados_validos(api_client):
    payload = {
        "nome": "Maria Souza",
        "documento": CPF_VALIDO_1,
        "telefone": "11999998888",
        "email": "maria@example.com",
        "ativo": True,
    }

    resposta = api_client.post("/api/clientes/", payload)

    assert resposta.status_code == status.HTTP_201_CREATED
    # Documento deve ser persistido sem mascara.
    assert resposta.data["documento"] == "11144477735"
    assert Cliente.objects.count() == 1


@pytest.mark.django_db
def test_criar_cliente_com_cpf_invalido_retorna_400(api_client):
    payload = {
        "nome": "Joao Silva",
        "documento": CPF_INVALIDO,
        "telefone": "11999998888",
        "email": "joao@example.com",
    }

    resposta = api_client.post("/api/clientes/", payload)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "documento" in resposta.data
    assert Cliente.objects.count() == 0


@pytest.mark.django_db
def test_criar_cliente_com_documento_duplicado_retorna_400(api_client):
    Cliente.objects.create(
        nome="Maria Souza",
        documento=CPF_VALIDO_1,
        telefone="11999998888",
        email="maria@example.com",
    )

    payload = {
        "nome": "Outra Pessoa",
        "documento": CPF_VALIDO_1,
        "telefone": "11988887777",
        "email": "outra@example.com",
    }

    resposta = api_client.post("/api/clientes/", payload)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "documento" in resposta.data
    assert Cliente.objects.count() == 1


@pytest.mark.django_db
def test_listar_clientes(api_client):
    Cliente.objects.create(
        nome="Ana", documento=CPF_VALIDO_1, telefone="11999998888", email="ana@example.com"
    )
    Cliente.objects.create(
        nome="Bruno", documento=CPF_VALIDO_2, telefone="11988887777", email="bruno@example.com"
    )

    resposta = api_client.get("/api/clientes/")

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 2


@pytest.mark.django_db
def test_desativar_cliente_via_patch(api_client):
    cliente = Cliente.objects.create(
        nome="Ana", documento=CPF_VALIDO_1, telefone="11999998888", email="ana@example.com"
    )

    resposta = api_client.patch(f"/api/clientes/{cliente.id}/", {"ativo": False})

    assert resposta.status_code == status.HTTP_200_OK
    cliente.refresh_from_db()
    assert cliente.ativo is False
