from django import forms
from .models import RegistroRefeicao

class RegistroRefeicaoForm(forms.ModelForm):
    class Meta:
        model = RegistroRefeicao
        fields = ['data_consumo', 'local', 'setor', 'qtd_cafe', 'qtd_almoco_buffet', 'qtd_almoco_marmita', 'qtd_janta', 'qtd_lanche']

        widgets = {
            'data_consumo': forms.DateInput(attrs={'type': 'date', 'class': 'input-dark'}),
            'local': forms.Select(attrs={'class': 'input-dark', 'id': 'dropLocal'}),
            'setor': forms.Select(attrs={'class': 'input-dark', 'id': 'dropSetor'}),
            'qtd_cafe': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_almoco_buffet': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_almoco_marmita': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_janta': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_lanche': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
        }