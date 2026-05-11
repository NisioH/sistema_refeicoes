from django import forms
from .models import RegistroRefeicao, TabelaPreco, LocalRefeicao, SetorColaborador


class RegistroRefeicaoForm(forms.ModelForm):
    class Meta:
        model = RegistroRefeicao
        fields = ['data_consumo', 'local', 'setor', 'qtd_cafe', 'qtd_almoco_buffet', 'qtd_almoco_marmita', 'qtd_janta',
                  'qtd_lanche']

        widgets = {
            'data_consumo': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'input-dark'}),
            'local': forms.Select(attrs={'class': 'input-dark', 'id': 'dropLocal'}),
            'setor': forms.Select(attrs={'class': 'input-dark', 'id': 'dropSetor'}),
            'qtd_cafe': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_almoco_buffet': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_almoco_marmita': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_janta': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
            'qtd_lanche': forms.NumberInput(attrs={'class': 'input-dark', 'min': '0'}),
        }

    def clean(self):
        """ Validação para impedir Terceiros Sede no Secador """
        cleaned_data = super().clean()
        local = cleaned_data.get('local')
        setor = cleaned_data.get('setor')

        # Regra: Se local for SECADOR, não pode ser TERCEIROS_FAZENDA (que agora aparece como Terceiros Sede)
        if local == LocalRefeicao.SECADOR and setor == SetorColaborador.TERCEIROS_FAZENDA:
            self.add_error('setor', "A opção 'Terceiros Sede' não é permitida para a Cantina do Secador.")

        return cleaned_data


class TabelaPrecoForm(forms.ModelForm):
    class Meta:
        model = TabelaPreco
        fields = ['cafe', 'buffet', 'marmita', 'janta', 'lanche']
        widgets = {
            'cafe': forms.NumberInput(attrs={'class': 'input-dark', 'step': '0.01'}),
            'buffet': forms.NumberInput(attrs={'class': 'input-dark', 'step': '0.01'}),
            'marmita': forms.NumberInput(attrs={'class': 'input-dark', 'step': '0.01'}),
            'janta': forms.NumberInput(attrs={'class': 'input-dark', 'step': '0.01'}),
            'lanche': forms.NumberInput(attrs={'class': 'input-dark', 'step': '0.01'}),
        }