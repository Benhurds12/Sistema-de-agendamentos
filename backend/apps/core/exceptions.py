from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def tratar_excecoes(exc, context):
    """Exception handler global do DRF.

    Sem isso, excluir um registro ainda referenciado por outro (ex.: um
    Cliente/Local/Tipo de Atendimento com Atendimento vinculado, protegidos
    via `on_delete=models.PROTECT`) sobe como `ProtectedError` e vira um
    500 com stack trace. A regra de negocio (nao pode excluir o que esta em
    uso) esta correta; aqui so convertemos isso em um 400 com mensagem
    legivel, no mesmo formato de erro do resto da API.
    """
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "nao_campo": [
                    "Nao e possivel excluir: este registro esta em uso por outro "
                    "cadastro (ex.: ha atendimentos vinculados). Desative-o em vez "
                    "de exclui-lo."
                ]
            },
            status=400,
        )

    return exception_handler(exc, context)
