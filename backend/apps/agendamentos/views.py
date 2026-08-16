from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import HorarioAgendamento
from .serializers import GerarGradeSerializer, HorarioAgendamentoSerializer
from .services import gerar_grade


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
