from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .filters import AtendimentoFilter
from .models import Atendimento, HorarioAgendamento, StatusAtendimento
from .serializers import (
    AlterarStatusSerializer,
    AtendimentoCreateSerializer,
    AtendimentoSerializer,
    AtualizarObservacoesSerializer,
    DataDisponivelSerializer,
    GerarGradeSerializer,
    HorarioAgendamentoSerializer,
)
from .services import alterar_status, atualizar_observacoes, gerar_grade, horarios_disponiveis_qs


class HorarioAgendamentoViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Grade de horarios: consulta + acao de geracao."""

    queryset = HorarioAgendamento.objects.select_related("local").all()
    serializer_class = HorarioAgendamentoSerializer
    filterset_fields = ["local", "disponivel"]

    @action(detail=False, methods=["post"], url_path="gerar-grade")
    def gerar_grade(self, request):
        entrada = GerarGradeSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        resultado = gerar_grade(
            local=entrada.validated_data["local"],
            inicio=entrada.validated_data["inicio"],
            fim=entrada.validated_data["fim"],
            duracao_minutos=entrada.validated_data["duracao_minutos"],
            apenas_dias_uteis=entrada.validated_data["apenas_dias_uteis"],
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


class AtendimentoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Agendamentos.

    Sem `update`/`destroy`: atendimentos nao sao editados livremente nem
    excluidos (regra do PDF — devem permanecer armazenados para consulta,
    independente do status). A unica alteracao possivel e a de status, que
    entra depois como uma action dedicada.
    """

    queryset = Atendimento.objects.select_related("cliente", "local", "tipo", "horario").all()
    filterset_class = AtendimentoFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # `?ordering=data_hora` (mais antigo primeiro) ou `?ordering=-data_hora`
    # (mais recente primeiro, default — igual ao `ordering` do model).
    ordering_fields = ["data_hora"]
    ordering = ["-data_hora"]

    def get_serializer_class(self):
        if self.action == "create":
            return AtendimentoCreateSerializer
        return AtendimentoSerializer

    def create(self, request, *args, **kwargs):
        entrada = self.get_serializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        atendimento = entrada.save()
        saida = AtendimentoSerializer(atendimento, context=self.get_serializer_context())
        return Response(saida.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="status")
    def alterar_status(self, request, pk=None):
        atendimento = self.get_object()
        entrada = AlterarStatusSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        atendimento = alterar_status(
            atendimento,
            entrada.validated_data["status"],
            motivo=entrada.validated_data.get("motivo", ""),
            descricao=entrada.validated_data.get("descricao", ""),
        )
        return Response(
            AtendimentoSerializer(atendimento, context=self.get_serializer_context()).data
        )

    @action(detail=True, methods=["patch"], url_path="observacoes")
    def observacoes(self, request, pk=None):
        """Edita motivo/descricao sem exigir transicao de status.

        Cobre o caso do status ter sido alterado pelo select da listagem
        (sem motivo/descricao) e o usuario querer complementar essa
        informacao depois — mesmo com o atendimento ja em status final.
        """
        atendimento = self.get_object()
        entrada = AtualizarObservacoesSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        atendimento = atualizar_observacoes(
            atendimento,
            motivo=entrada.validated_data.get("motivo"),
            descricao=entrada.validated_data.get("descricao"),
        )
        return Response(
            AtendimentoSerializer(atendimento, context=self.get_serializer_context()).data
        )

    @action(detail=False, methods=["get"])
    def indicadores(self, request):
        """Cards do topo da listagem.

        Usa `self.filter_queryset(...)`, ou seja, os MESMOS filtros que a
        listagem principal aplicou (status, local, tipo, cliente_nome) — os
        indicadores sempre refletem o recorte atual da tela, como pede o PDF.
        """
        qs = self.filter_queryset(self.get_queryset())
        dados = qs.aggregate(
            total=Count("id"),
            pendentes=Count("id", filter=Q(status=StatusAtendimento.PENDENTE)),
            realizados=Count("id", filter=Q(status=StatusAtendimento.REALIZADO)),
            cancelados=Count("id", filter=Q(status=StatusAtendimento.CANCELADO)),
            nao_compareceram=Count(
                "id", filter=Q(status=StatusAtendimento.NAO_COMPARECEU)
            ),
        )
        return Response(dados)
