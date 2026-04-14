from rest_framework import serializers
from .models import RegistroRefeicao

class RegistroRefeicaoSerializer(serializers.ModelSerializer):
    total_dia = serializers.ReadOnlyField(source='total_gasto')
    data_pt_br = serializers.ReadOnlyField(source='data_formatada')

    class Meta:
        model = RegistroRefeicao
        fields = '__all__'