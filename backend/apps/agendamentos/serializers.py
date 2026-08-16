from rest_framework import serializers

from apps.locais.models import Local

from .models import HorarioAgendamento


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


class DataDisponivelSerializer(serializers.Serializer):
    """Uma linha do agrupamento por dia (usado no passo 2 do novo agendamento)."""

    data = serializers.DateField()
    total_horarios = serializers.IntegerField()
