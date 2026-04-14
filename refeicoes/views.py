from rest_framework import viewsets
from .models import RegistroRefeicao
from .serializers import RegistroRefeicaoSerializer

class RegistroRefeicaoViewSet(viewsets.ModelViewSet):
    """Criação automática de Listar, Criar, Editar e Deletar refeições"""

    queryset = RegistroRefeicao.objects.all().order_by('-data_consumo')
    serializer_class = RegistroRefeicaoSerializer

