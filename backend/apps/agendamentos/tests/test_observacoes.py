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
def test_motivo_em_atendimento_pendente_retorna_400(api_client, atendimento):
    """Motivo de cancelamento so faz sentido em atendimento CANCELADO (regra do PDF)."""
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/", {"motivo": "Cliente remarcou."}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST
    atendimento.refresh_from_db()
    assert atendimento.motivo == ""


@pytest.mark.django_db
def test_descricao_em_atendimento_pendente_retorna_400(api_client, atendimento):
    """Relatorio so faz sentido em atendimento REALIZADO (regra do PDF)."""
    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/", {"descricao": "Nota qualquer."}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST
    atendimento.refresh_from_db()
    assert atendimento.descricao == ""


@pytest.mark.django_db
def test_descricao_em_atendimento_cancelado_retorna_400(api_client, atendimento):
    api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.CANCELADO}
    )

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/", {"descricao": "Nota qualquer."}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_motivo_em_atendimento_realizado_retorna_400(api_client, atendimento):
    api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.REALIZADO}
    )

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/", {"motivo": "Nao devia aceitar."}
    )

    assert resposta.status_code == http_status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_editar_observacoes_com_atendimento_em_status_final(api_client, atendimento):
    """Caso central do pedido: status ja cancelado pelo select, motivo vem depois."""
    api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.CANCELADO}
    )
    atendimento.refresh_from_db()
    assert atendimento.motivo == ""  # confirma que o select nao mandou motivo

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/",
        {"motivo": "Cliente remarcou para semana seguinte."},
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    atendimento.refresh_from_db()
    assert atendimento.status == StatusAtendimento.CANCELADO
    assert atendimento.motivo == "Cliente remarcou para semana seguinte."


@pytest.mark.django_db
def test_editar_descricao_com_atendimento_realizado(api_client, atendimento):
    api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.REALIZADO}
    )

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/",
        {"descricao": "Atendimento correu bem, sem intercorrencias."},
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    atendimento.refresh_from_db()
    assert atendimento.descricao == "Atendimento correu bem, sem intercorrencias."


@pytest.mark.django_db
def test_editar_observacoes_pode_sobrescrever_valor_existente(api_client, atendimento):
    api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/",
        {"status": StatusAtendimento.CANCELADO, "motivo": "Motivo original."},
    )

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/", {"motivo": "Motivo corrigido."}
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    atendimento.refresh_from_db()
    assert atendimento.motivo == "Motivo corrigido."


@pytest.mark.django_db
def test_editar_observacoes_nao_altera_status(api_client, atendimento):
    api_client.patch(
        f"/api/atendimentos/{atendimento.id}/status/", {"status": StatusAtendimento.CANCELADO}
    )

    resposta = api_client.patch(
        f"/api/atendimentos/{atendimento.id}/observacoes/", {"motivo": "Nota qualquer."}
    )

    assert resposta.status_code == http_status.HTTP_200_OK
    assert resposta.data["status"] == StatusAtendimento.CANCELADO


@pytest.mark.django_db
def test_editar_observacoes_sem_campos_nao_falha(api_client, atendimento):
    resposta = api_client.patch(f"/api/atendimentos/{atendimento.id}/observacoes/", {})

    assert resposta.status_code == http_status.HTTP_200_OK
