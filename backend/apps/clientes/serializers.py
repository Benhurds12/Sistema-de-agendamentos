from rest_framework import serializers

from .models import Cliente
from .validators import somente_digitos, validar_documento


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id",
            "nome",
            "documento",
            "telefone",
            "email",
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

    def validate_documento(self, value: str) -> str:
        digitos = somente_digitos(value)
        # Levanta django.core.exceptions.ValidationError se o digito
        # verificador nao bater; o DRF converte isso automaticamente
        # para o formato de erro da API.
        validar_documento(digitos)

        query = Cliente.objects.filter(documento=digitos)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("Ja existe um cliente com este documento.")

        return digitos
