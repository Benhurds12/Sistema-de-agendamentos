import pytest
from rest_framework import status

from apps.clientes.models import Cliente

CPF_VALIDO_1 = "111.444.777-35"
CPF_VALIDO_2 = "529.982.247-25"
CPF_INVALIDO = "111.111.111-11"


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
def test_editar_cliente_via_put(api_client):
    cliente = Cliente.objects.create(
        nome="Ana", documento=CPF_VALIDO_1, telefone="11999998888", email="ana@example.com"
    )

    payload = {
        "nome": "Ana Souza",
        "documento": CPF_VALIDO_1,
        "telefone": "11977776666",
        "email": "ana.souza@example.com",
    }
    resposta = api_client.put(f"/api/clientes/{cliente.id}/", payload)

    assert resposta.status_code == status.HTTP_200_OK
    cliente.refresh_from_db()
    assert cliente.nome == "Ana Souza"
    assert cliente.telefone == "11977776666"
    assert cliente.email == "ana.souza@example.com"


@pytest.mark.django_db
def test_editar_cliente_com_documento_de_outro_cliente_retorna_400(api_client):
    Cliente.objects.create(
        nome="Ana", documento=CPF_VALIDO_1, telefone="11999998888", email="ana@example.com"
    )
    bruno = Cliente.objects.create(
        nome="Bruno", documento=CPF_VALIDO_2, telefone="11988887777", email="bruno@example.com"
    )

    resposta = api_client.put(
        f"/api/clientes/{bruno.id}/",
        {
            "nome": "Bruno",
            "documento": CPF_VALIDO_1,
            "telefone": "11988887777",
            "email": "bruno@example.com",
        },
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "documento" in resposta.data


@pytest.mark.django_db
def test_desativar_cliente_via_patch(api_client):
    cliente = Cliente.objects.create(
        nome="Ana", documento=CPF_VALIDO_1, telefone="11999998888", email="ana@example.com"
    )

    resposta = api_client.patch(f"/api/clientes/{cliente.id}/", {"ativo": False})

    assert resposta.status_code == status.HTTP_200_OK
    cliente.refresh_from_db()
    assert cliente.ativo is False


@pytest.mark.django_db
def test_excluir_cliente_sem_atendimentos_e_permitido(api_client):
    cliente = Cliente.objects.create(
        nome="Ana", documento=CPF_VALIDO_1, telefone="11999998888", email="ana@example.com"
    )

    resposta = api_client.delete(f"/api/clientes/{cliente.id}/")

    assert resposta.status_code == status.HTTP_204_NO_CONTENT
    assert Cliente.objects.count() == 0


@pytest.mark.django_db
def test_excluir_cliente_com_atendimento_retorna_400_amigavel(api_client):
    """Antes disso, um ProtectedError nao tratado subia como 500 com stack trace."""
    from datetime import timedelta

    from django.utils import timezone

    from apps.agendamentos.models import Atendimento, HorarioAgendamento
    from apps.locais.models import Local
    from apps.tipos_atendimento.models import TipoAtendimento

    cliente = Cliente.objects.create(
        nome="Ana", documento=CPF_VALIDO_1, telefone="11999998888", email="ana@example.com"
    )
    local = Local.objects.create(nome="Unidade Central", endereco="Rua A, 1")
    tipo = TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)
    inicio = timezone.now() + timedelta(days=1)
    horario = HorarioAgendamento.objects.create(
        local=local, inicio=inicio, fim=inicio + timedelta(minutes=30), disponivel=False
    )
    Atendimento.objects.create(
        cliente=cliente, local=local, tipo=tipo, horario=horario, data_hora=inicio
    )

    resposta = api_client.delete(f"/api/clientes/{cliente.id}/")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "nao_campo" in resposta.data
    assert Cliente.objects.filter(id=cliente.id).exists()
