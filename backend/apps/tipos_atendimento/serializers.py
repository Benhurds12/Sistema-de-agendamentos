from rest_framework import serializers

from .models import TipoAtendimento


class TipoAtendimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAtendimento
        fields = [
            "id",
            "nome",
            "descricao",
            "duracao_minutos",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]

    def validate_nome(self, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Nome deve ter ao menos 3 caracteres.")
        return value

    def validate_duracao_minutos(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Duracao deve ser maior que zero.")
        return value
