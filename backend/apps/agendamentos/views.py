from django.db.models import Count
from django.db.models.functions import TruncDate
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import HorarioAgendamento
from .serializers import (
    DataDisponivelSerializer,
    GerarGradeSerializer,
    HorarioAgendamentoSerializer,
)
from .services import gerar_grade, horarios_disponiveis_qs


class HorarioAgendamentoViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Grade de horarios: consulta + acao de geracao."""

    queryset = HorarioAgendamento.objects.select_related("local").all()
    serializer_class = HorarioAgendamentoSerializer

    @action(detail=False, methods=["post"], url_path="gerar-grade")
    def gerar_grade(self, request):
        entrada = GerarGradeSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        resultado = gerar_grade(
            local=entrada.validated_data["local"],
            inicio=entrada.validated_data["inicio"],
            fim=entrada.validated_data["fim"],
            duracao_minutos=entrada.validated_data["duracao_minutos"],
        )

        return Response(
            {"criadas": resultado.criadas, "mensagem": resultado.mensagem},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="datas-disponiveis")
    def datas_disponiveis(self, request):
        """Passo 2 do novo agendamento: quais dias tem vaga para o local."""
        local_id = request.query_params.get("local")
        if not local_id:
            raise ValidationError({"local": ["Informe o local para consultar as datas."]})

        dados = (
            horarios_disponiveis_qs(local_id)
            .annotate(data=TruncDate("inicio"))
            .values("data")
            .annotate(total_horarios=Count("id"))
            .order_by("data")
        )
        return Response(DataDisponivelSerializer(dados, many=True).data)

    @action(detail=False, methods=["get"], url_path="horarios-disponiveis")
    def horarios_disponiveis(self, request):
        """Passo 3 do novo agendamento: horarios livres numa data especifica."""
        local_id = request.query_params.get("local")
        data = request.query_params.get("data")
        if not local_id or not data:
            raise ValidationError(
                {"nao_campo": ["Informe o local e a data para consultar os horarios."]}
            )

        qs = horarios_disponiveis_qs(local_id).filter(inicio__date=data)
        return Response(HorarioAgendamentoSerializer(qs, many=True).data)
