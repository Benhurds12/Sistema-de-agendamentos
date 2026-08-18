from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.agendamentos.models import Atendimento, HorarioAgendamento, StatusAtendimento
from apps.clientes.models import Cliente
from apps.locais.models import Local
from apps.tipos_atendimento.models import TipoAtendimento


@pytest.fixture
def local() -> Local:
    return Local.objects.create(nome="Unidade Central", endereco="Rua A, 1")


@pytest.fixture
def cliente() -> Cliente:
    return Cliente.objects.create(
        nome="Maria Souza", documento="11144477735", telefone="11999998888",
        email="maria@example.com",
    )


@pytest.fixture
def tipo() -> TipoAtendimento:
    return TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)


@pytest.fixture
def horario(local) -> HorarioAgendamento:
    inicio = timezone.now() + timedelta(days=1)
    return HorarioAgendamento.objects.create(
        local=local, inicio=inicio, fim=inicio + timedelta(minutes=30)
    )


def _payload(cliente, local, tipo, horario, **extra):
    return {
        "cliente": cliente.id,
        "local": local.id,
        "tipo": tipo.id,
        "horario": horario.id,
        **extra,
    }


@pytest.mark.django_db
def test_criar_atendimento_marca_horario_como_indisponivel(
    api_client, cliente, local, tipo, horario
):
    resposta = api_client.post("/api/atendimentos/", _payload(cliente, local, tipo, horario))

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["status"] == StatusAtendimento.PENDENTE
    horario.refresh_from_db()
    assert horario.disponivel is False
    assert Atendimento.objects.count() == 1


@pytest.mark.django_db
def test_agendar_horario_ja_utilizado_retorna_400(api_client, cliente, local, tipo, horario):
    primeira = api_client.post("/api/atendimentos/", _payload(cliente, local, tipo, horario))
    assert primeira.status_code == status.HTTP_201_CREATED

    outro_cliente = Cliente.objects.create(
        nome="Joao Silva", documento="52998224725", telefone="11988887777",
        email="joao@example.com",
    )
    segunda = api_client.post(
        "/api/atendimentos/", _payload(outro_cliente, local, tipo, horario)
    )

    assert segunda.status_code == status.HTTP_400_BAD_REQUEST
    assert "horario" in segunda.data
    assert Atendimento.objects.count() == 1


@pytest.mark.django_db
def test_agendar_com_horario_de_outro_local_retorna_400(
    api_client, cliente, local, tipo, horario
):
    outro_local = Local.objects.create(nome="Unidade Sul", endereco="Rua B, 2")

    resposta = api_client.post(
        "/api/atendimentos/", _payload(cliente, outro_local, tipo, horario)
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "horario" in resposta.data


@pytest.mark.django_db
def test_agendar_horario_no_passado_retorna_400(api_client, cliente, local, tipo):
    inicio_passado = timezone.now() - timedelta(hours=1)
    horario_passado = HorarioAgendamento.objects.create(
        local=local, inicio=inicio_passado, fim=inicio_passado + timedelta(minutes=30)
    )

    resposta = api_client.post(
        "/api/atendimentos/", _payload(cliente, local, tipo, horario_passado)
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "horario" in resposta.data


@pytest.mark.django_db
def test_agendar_com_cliente_inativo_retorna_400(api_client, cliente, local, tipo, horario):
    cliente.ativo = False
    cliente.save(update_fields=["ativo"])

    resposta = api_client.post("/api/atendimentos/", _payload(cliente, local, tipo, horario))

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "cliente" in resposta.data


@pytest.mark.django_db
def test_atendimento_criado_nao_aparece_mais_em_horarios_disponiveis(
    api_client, cliente, local, tipo, horario
):
    api_client.post("/api/atendimentos/", _payload(cliente, local, tipo, horario))

    data_str = timezone.localtime(horario.inicio).date().isoformat()
    resposta = api_client.get(
        f"/api/horarios/horarios-disponiveis/?local={local.id}&data={data_str}"
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 0
