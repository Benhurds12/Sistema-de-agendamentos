from rest_framework import serializers

from apps.clientes.models import Cliente
from apps.locais.models import Local
from apps.tipos_atendimento.models import TipoAtendimento

from .models import Atendimento, HorarioAgendamento, StatusAtendimento
from .services import criar_atendimento


class HorarioAgendamentoSerializer(serializers.ModelSerializer):
    local_nome = serializers.CharField(source="local.nome", read_only=True)

    class Meta:
        model = HorarioAgendamento
        fields = ["id", "local", "local_nome", "inicio", "fim", "disponivel"]
        read_only_fields = fields


class GerarGradeSerializer(serializers.Serializer):
    """Entrada da tela de geracao de grade."""

    local = serializers.PrimaryKeyRelatedField(queryset=Local.objects.all())
    inicio = serializers.DateTimeField()
    fim = serializers.DateTimeField()
    duracao_minutos = serializers.IntegerField(min_value=1)
    apenas_dias_uteis = serializers.BooleanField(required=False, default=False)


class DataDisponivelSerializer(serializers.Serializer):
    """Uma linha do agrupamento por dia (usado no passo 2 do novo agendamento)."""

    data = serializers.DateField()
    total_horarios = serializers.IntegerField()


class AtendimentoSerializer(serializers.ModelSerializer):
    """Leitura: usado na resposta de criacao e, futuramente, na listagem."""

    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)
    local_nome = serializers.CharField(source="local.nome", read_only=True)
    tipo_nome = serializers.CharField(source="tipo.nome", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    transicoes_permitidas = serializers.SerializerMethodField()

    class Meta:
        model = Atendimento
        fields = [
            "id",
            "cliente",
            "cliente_nome",
            "local",
            "local_nome",
            "tipo",
            "tipo_nome",
            "horario",
            "data_hora",
            "motivo",
            "descricao",
            "status",
            "status_display",
            "transicoes_permitidas",
            "criado_em",
        ]
        read_only_fields = fields

    def get_transicoes_permitidas(self, obj) -> list[str]:
        return sorted(
            candidato
            for candidato in StatusAtendimento.values
            if obj.pode_alterar_para(candidato)
        )


class AtendimentoCreateSerializer(serializers.Serializer):
    """Criacao de agendamento: delega a reserva do horario ao service."""

    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    local = serializers.PrimaryKeyRelatedField(queryset=Local.objects.all())
    tipo = serializers.PrimaryKeyRelatedField(queryset=TipoAtendimento.objects.all())
    horario = serializers.PrimaryKeyRelatedField(queryset=HorarioAgendamento.objects.all())
    descricao = serializers.CharField(required=False, allow_blank=True, default="")
    motivo = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated_data):
        return criar_atendimento(
            cliente=validated_data["cliente"],
            local=validated_data["local"],
            tipo=validated_data["tipo"],
            horario_id=validated_data["horario"].pk,
            descricao=validated_data.get("descricao", ""),
            motivo=validated_data.get("motivo", ""),
        )


class AlterarStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StatusAtendimento.choices)
    motivo = serializers.CharField(required=False, allow_blank=True, default="")
    descricao = serializers.CharField(required=False, allow_blank=True, default="")


class AtualizarObservacoesSerializer(serializers.Serializer):
    """Edicao de motivo/descricao sem mudar o status (ver `atualizar_observacoes`)."""

    motivo = serializers.CharField(required=False, allow_blank=True)
    descricao = serializers.CharField(required=False, allow_blank=True)
