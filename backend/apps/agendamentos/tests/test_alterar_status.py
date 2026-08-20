from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status as http_status

from apps.agendamentos.models import Atendimento, HorarioAgendamento, StatusAtendimento
from apps.clientes.models import Cliente
from apps.locais.models import Local
from apps.tipos_atendimento.models import TipoAtendimento


@pytest.fixture
def atendimento() -> Atendimento:
    local = Local.objects.create(nome="Unidade Central", endereco="Rua A, 1")
    cliente = Cliente.objects.create(
        nome="Maria Souza", documento="11144477735", telefone="11999998888",
        email="maria@example.com",
    )
    tipo = TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)
    inicio = timezone.now() + timedelta(days=1)
    horario = HorarioAgendamento.objects.create(
        local=local, inicio=inicio, fim=inicio + timedelta(minutes=30), disponivel=False
    )
    return Atendimento.objects.create(
        cliente=cliente, local=local, tipo=tipo, horario=horario, data_hora=inicio
    )


@pytest.mark.django_db
def test_atendimento_nasce_pendente(atendimento):
    assert atendimento.status == StatusAtendimento.PENDENTE


@pytest.mark.django_db
def test_pendente_para_realizado_com_descricao(api_client, atendimento):
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/",
        {"status": StatusAtendimento.REALIZADO, "descricao": "Atendimento concluido sem intercorrencias."},
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    assert resposta.data["status"] == StatusAtendimento.REALIZADO
    assert resposta.data["descricao"] == "Atendimento concluido sem intercorrencias."


@pytest.mark.django_db
def test_pendente_para_cancelado_com_motivo(api_client, atendimento):
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/",
        {"status": StatusAtendimento.CANCELADO, "motivo": "Cliente remarcou para outra data."},
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    assert resposta.data["status"] == StatusAtendimento.CANCELADO
    assert resposta.data["motivo"] == "Cliente remarcou para outra data."


@pytest.mark.django_db
def test_motivo_e_descricao_sao_opcionais(api_client, atendimento):
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/",
        {"status": StatusAtendimento.NAO_COMPARECEU},
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    assert resposta.data["status"] == StatusAtendimento.NAO_COMPARECEU


@pytest.mark.parametrize(
    "status_final",
    [StatusAtendimento.REALIZADO, StatusAtendimento.CANCELADO, StatusAtendimento.NAO_COMPARECEU],
)
@pytest.mark.django_db
def test_status_final_nao_aceita_transicao_arbitraria(api_client, atendimento, status_final):
    """REALIZADO e NAO_COMPARECEU sao definitivos; CANCELADO so aceita voltar
    a PENDENTE (testado a parte), nao pular para qualquer outro status."""
    api_client.patch(f"/api/atendimentos/{atendimento.id}/status/", {"status": status_final})

    # Tenta mudar para um status que nunca e permitido a partir daqui.
    outro_status = (
        StatusAtendimento.REALIZADO
        if status_final != StatusAtendimento.REALIZADO
        else StatusAtendimento.NAO_COMPARECEU
    )
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": outro_status}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST
    assert "status" in resposta.data


@pytest.mark.django_db
def test_cancelado_pode_reabrir_para_pendente_se_horario_ainda_nao_passou(api_client, atendimento):
    """`atendimento` (fixture) tem horario no futuro (+1 dia)."""
    api_client.patch(f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.CANCELADO})

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.PENDENTE}
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    assert resposta.data["status"] == StatusAtendimento.PENDENTE
    assert "PENDENTE" not in resposta.data["transicoes_permitidas"]  # ja esta nele


@pytest.mark.django_db
def test_cancelado_nao_pode_reabrir_se_horario_ja_passou(api_client):
    local = Local.objects.create(nome="Unidade Central", endereco="Rua A, 1")
    cliente = Cliente.objects.create(
        nome="Maria Souza", documento="11144477735", telefone="11999998888",
        email="maria@example.com",
    )
    tipo = TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)
    inicio = timezone.now() - timedelta(hours=2)
    horario = HorarioAgendamento.objects.create(
        local=local, inicio=inicio, fim=inicio + timedelta(minutes=30), disponivel=False
    )
    atendimento_passado = Atendimento.objects.create(
        cliente=cliente, local=local, tipo=tipo, horario=horario, data_hora=inicio,
        status=StatusAtendimento.CANCELADO,
    )

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento_passado.id}/status/", {"status": StatusAtendimento.PENDENTE}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST
    assert "ja passou" in resposta.data["status"][0]


@pytest.mark.django_db
def test_transicoes_permitidas_nao_lista_pendente_para_cancelado_com_horario_passado(api_client):
    local = Local.objects.create(nome="Unidade Central", endereco="Rua A, 1")
    cliente = Cliente.objects.create(
        nome="Maria Souza", documento="11144477735", telefone="11999998888",
        email="maria@example.com",
    )
    tipo = TipoAtendimento.objects.create(nome="Consulta", duracao_minutos=30)
    inicio = timezone.now() - timedelta(hours=2)
    horario = HorarioAgendamento.objects.create(
        local=local, inicio=inicio, fim=inicio + timedelta(minutes=30), disponivel=False
    )
    atendimento_passado = Atendimento.objects.create(
        cliente=cliente, local=local, tipo=tipo, horario=horario, data_hora=inicio,
        status=StatusAtendimento.CANCELADO,
    )

    resposta = api_client.get(f"/api/atendimentos/{atendimento_passado.id}/")

    assert resposta.data["transicoes_permitidas"] == []


@pytest.mark.django_db
def test_alterar_para_o_mesmo_status_retorna_400(api_client, atendimento):
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.PENDENTE}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_cancelar_nao_libera_o_horario(api_client, atendimento):
    """Decisao de negocio explicita: horario usado fica indisponivel para sempre."""
    api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.CANCELADO}
    )

    atendimento.horario.refresh_from_db()
    assert atendimento.horario.disponivel is False


@pytest.mark.django_db
def test_status_invalido_retorna_400(api_client, atendimento):
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": "EM_ANDAMENTO"}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST
