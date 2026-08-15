from rest_framework import serializers

from .models import Local


class LocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Local
        fields = [
            "id",
            "nome",
            "descricao",
            "endereco",
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

    def validate_endereco(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Endereco e obrigatorio.")
        return value
