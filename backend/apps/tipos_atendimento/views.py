from rest_framework import viewsets

from .models import TipoAtendimento
from .serializers import TipoAtendimentoSerializer


class TipoAtendimentoViewSet(viewsets.ModelViewSet):
    queryset = TipoAtendimento.objects.all()
    serializer_class = TipoAtendimentoSerializer
