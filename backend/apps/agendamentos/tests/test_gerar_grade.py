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


def _dias_a_partir_de_amanha_as(dias: int, hora: int, minuto: int = 0):
    """Horario `dias` apos amanha (0 = amanha, 1 = depois de amanha, ...)."""
    base = timezone.localtime() + timedelta(days=1 + dias)
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
def test_grade_multidias_respeita_janela_diaria_e_nao_cruza_a_madrugada(api_client, local):
    """Ex. do usuario: dia 1 as 08:00 ate dia 5 as 18:00 -> so gera horarios
    entre 08:00 e 18:00 em CADA um dos 5 dias, nunca durante a madrugada."""
    inicio = _dias_a_partir_de_amanha_as(0, 8, 0)
    fim = _dias_a_partir_de_amanha_as(4, 18, 0)  # 5 dias (0,1,2,3,4)

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 60,
        },
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    # 10h de expediente (08h-18h) / 60min = 10 horarios por dia * 5 dias
    assert resposta.data["criadas"] == 50

    horarios = HorarioAgendamento.objects.filter(local=local).order_by("inicio")
    assert horarios.count() == 50
    for horario in horarios:
        hora_local = timezone.localtime(horario.inicio)
        assert 8 <= hora_local.hour < 18, (
            f"horario {hora_local} caiu fora do expediente (08h-18h)"
        )
        fim_local = timezone.localtime(horario.fim)
        assert fim_local.hour <= 18


@pytest.mark.django_db
def test_grade_multidias_janela_diaria_invalida_retorna_400(api_client, local):
    """Fim as 08:00 e inicio as 18:00 (no dia) nao formam expediente valido."""
    inicio = _dias_a_partir_de_amanha_as(0, 18, 0)
    fim = _dias_a_partir_de_amanha_as(1, 8, 0)

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
    assert "fim" in resposta.data


@pytest.mark.django_db
def test_grade_multidias_ignora_horario_existente_fora_do_expediente(api_client, local):
    """Um horario as 22h (fora de 08h-18h) num dos dias do intervalo NAO
    deveria bloquear a geracao da grade diurna."""
    horario_noturno = _dias_a_partir_de_amanha_as(1, 22, 0)
    HorarioAgendamento.objects.create(
        local=local, inicio=horario_noturno, fim=horario_noturno + timedelta(minutes=30)
    )

    inicio = _dias_a_partir_de_amanha_as(0, 8, 0)
    fim = _dias_a_partir_de_amanha_as(2, 18, 0)  # 3 dias

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 60,
        },
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["criadas"] == 30  # 10 horarios/dia * 3 dias


@pytest.mark.django_db
def test_grade_multidias_detecta_conflito_dentro_do_expediente(api_client, local):
    """Um horario as 09h num dos dias (dentro de 08h-18h) deve bloquear a
    geracao inteira, mesmo o conflito estando so em 1 dos varios dias."""
    horario_conflitante = _dias_a_partir_de_amanha_as(1, 9, 0)
    HorarioAgendamento.objects.create(
        local=local,
        inicio=horario_conflitante,
        fim=horario_conflitante + timedelta(minutes=30),
    )

    inicio = _dias_a_partir_de_amanha_as(0, 8, 0)
    fim = _dias_a_partir_de_amanha_as(2, 18, 0)

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 60,
        },
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    # So o horario de conflito original continua existindo; nada foi criado.
    assert HorarioAgendamento.objects.filter(local=local).count() == 1


@pytest.mark.django_db
def test_grade_apenas_dias_uteis_pula_sabado_e_domingo(api_client, local):
    inicio = _dias_a_partir_de_amanha_as(0, 8, 0)
    fim = _dias_a_partir_de_amanha_as(7, 18, 0)  # 8 dias corridos: cobre >=1 fim de semana

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 60,
            "apenas_dias_uteis": True,
        },
    )

    assert resposta.status_code == status.HTTP_201_CREATED

    dias_uteis_no_intervalo = sum(
        1
        for i in range(8)
        if (inicio.date() + timedelta(days=i)).weekday() not in (5, 6)
    )
    assert resposta.data["criadas"] == dias_uteis_no_intervalo * 10  # 10h / 60min por dia

    horarios = HorarioAgendamento.objects.filter(local=local)
    for horario in horarios:
        dia_semana = timezone.localtime(horario.inicio).weekday()
        assert dia_semana not in (5, 6), f"horario caiu em fim de semana: {horario.inicio}"


@pytest.mark.django_db
def test_grade_sem_flag_inclui_fim_de_semana_normalmente(api_client, local):
    """Comportamento padrao (flag ausente/False): nao filtra nenhum dia."""
    inicio = _dias_a_partir_de_amanha_as(0, 8, 0)
    fim = _dias_a_partir_de_amanha_as(7, 18, 0)

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 60,
        },
    )

    assert resposta.status_code == status.HTTP_201_CREATED
    assert resposta.data["criadas"] == 80  # 8 dias * 10 horarios/dia, sem excecao


@pytest.mark.django_db
def test_grade_apenas_dias_uteis_sem_nenhum_dia_util_retorna_400(api_client, local):
    """Se o intervalo cai inteiro num fim de semana, nao ha nada para gerar."""
    amanha = timezone.localtime().date() + timedelta(days=1)
    dias_ate_sabado = (5 - amanha.weekday()) % 7
    sabado = amanha + timedelta(days=dias_ate_sabado)

    inicio = timezone.localtime().replace(
        year=sabado.year, month=sabado.month, day=sabado.day,
        hour=8, minute=0, second=0, microsecond=0,
    )
    fim = inicio + timedelta(days=1, hours=10)  # sabado 08:00 ate domingo 18:00

    resposta = api_client.post(
        "/api/horarios/gerar-grade/",
        {
            "local": local.id,
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "duracao_minutos": 60,
            "apenas_dias_uteis": True,
        },
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "apenas_dias_uteis" in resposta.data
    assert HorarioAgendamento.objects.filter(local=local).count() == 0


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
