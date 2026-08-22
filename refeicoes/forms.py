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

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super(RegistroRefeicaoForm, self).__init__(*args, **kwargs)

        fazenda_nome = None
        is_dono = True

        if self.usuario and hasattr(self.usuario, 'perfil'):
            is_dono = self.usuario.perfil.is_dono
            if self.usuario.perfil.fazenda_lotacao:
                fazenda_nome = self.usuario.perfil.fazenda_lotacao.nome

        # =========================================================
        # SOLUÇÃO DEFINITIVA (FORÇA BRUTA)
        # Se só tem 1 opção, já carrega direto sem o "Selecione..."
        # Injetamos os valores exatos para o Django não se perder.
        # =========================================================

        if fazenda_nome == 'Fazenda Matão' and not is_dono:
            self.fields['local'].choices = [(LocalRefeicao.CANTINA_MATAO, 'Cantina Matão')]
            self.fields['setor'].choices = [
                (SetorColaborador.CORPORATIVO, 'Corporativo'),
                (SetorColaborador.TERCEIROS, 'Terceiros')
            ]

        elif fazenda_nome == 'Fazenda BC' and not is_dono:
            self.fields['local'].choices = [(LocalRefeicao.CANTINA_BC, 'Cantina BC')]
            self.fields['setor'].choices = [
                (SetorColaborador.CORPORATIVO, 'Corporativo'),
                (SetorColaborador.TERCEIROS, 'Terceiros')
            ]

        elif fazenda_nome == 'Fazenda Lagoa' and not is_dono:
            self.fields['local'].choices = [(LocalRefeicao.CANTINA_LAGOA, 'Cantina Lagoa')]
            self.fields['setor'].choices = [
                (SetorColaborador.CORPORATIVO, 'Corporativo'),
                (SetorColaborador.TERCEIROS, 'Terceiros')
            ]

        elif fazenda_nome in ['Fazenda Independência', 'Fazenda Independencia'] and not is_dono:
            # Como a matriz tem 2 cantinas e vários setores, aqui MANTEMOS o "Selecione..."
            self.fields['local'].choices = [
                ('', '--- Selecione a Cantina ---'),
                (LocalRefeicao.SEDE, 'Cantina Sede'),
                (LocalRefeicao.SECADOR, 'Cantina Secador')
            ]
            self.fields['setor'].choices = [
                ('', '--- Selecione o Setor ---'),
                (SetorColaborador.COLAB_SECADOR, 'Colaborador Secador'),
                (SetorColaborador.SAFRISTA_SECADOR, 'Safrista Secador'),
                (SetorColaborador.COLAB_ALGODOEIRA, 'Colaborador Algodoeira'),
                (SetorColaborador.TERC_ALGODOEIRA, 'Terceirizado Algodoeira'),
                (SetorColaborador.SAFRISTA_ALGODOEIRA, 'Safrista Algodoeira'),
                (SetorColaborador.COLAB_SEDE, 'Colaborador Sede'),
                (SetorColaborador.TERCEIROS_FAZENDA, 'Terceirizado Sede'),
                (SetorColaborador.COLAB_ESCRITORIO, 'Colaborador Escritório')
            ]
        else:
            # Para o Administrador (Você), mostra tudo, com "Selecione..." para evitar lançamento acidental
            self.fields['local'].choices = [('', '--- Selecione a Cantina ---')] + list(LocalRefeicao.choices)
            self.fields['setor'].choices = [('', '--- Selecione o Setor ---')] + [c for c in SetorColaborador.choices if
                                                                                  c[
                                                                                      0] != SetorColaborador.CORPORATIVO_SEDE]

    def clean(self):
        cleaned_data = super().clean()
        local = cleaned_data.get('local')
        setor = cleaned_data.get('setor')

        if local == LocalRefeicao.SECADOR and setor == SetorColaborador.TERCEIROS_FAZENDA:
            self.add_error('setor', "A opção 'Terceirizado Sede' não é permitida para a Cantina do Secador.")

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