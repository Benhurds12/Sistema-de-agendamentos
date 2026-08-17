from django_filters.rest_framework import CharFilter, ChoiceFilter, FilterSet, NumberFilter

from .models import Atendimento, StatusAtendimento


class AtendimentoFilter(FilterSet):
    """Filtros da tela de listagem. Podem ser usados isolados ou combinados."""

    status = ChoiceFilter(choices=StatusAtendimento.choices)
    local = NumberFilter(field_name="local_id")
    tipo = NumberFilter(field_name="tipo_id")
    cliente_nome = CharFilter(field_name="cliente__nome", lookup_expr="icontains")

    class Meta:
        model = Atendimento
        fields = ["status", "local", "tipo", "cliente_nome"]
