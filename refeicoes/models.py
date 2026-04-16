from django.db import models
from django.utils import timezone
from decimal import Decimal


class TabelaPreco(models.Model):
    cafe = models.DecimalField("Caf'da Manhã", max_digits=5, decimal_places=2, default=9.00)
    buffet = models.DecimalField("Almoço Buffet", max_digits=5, decimal_places=2, default=24.00)
    marmita = models.DecimalField("Almoço Marmita", max_digits=5, decimal_places=2, default=21.50)
    janta = models.DecimalField("Janta", max_digits=5, decimal_places=2, default=21.50)
    lanche = models.DecimalField("Lanche", max_digits=5, decimal_places=2, default=9.00)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tabela Preço"
        verbose_name_plural = "Tabela Preços"

    def __str__(self):
        return  f"Preços vigentes (Atualizado em {self.data_atualizacao.strtime('%d/%m/%Y')})"

class LocalRefeicao(models.TextChoices):
    SEDE = 'SEDE', 'Cantina da Sede'
    SECADOR = 'SECADOR', 'Cantina da Secador'

class SetorColaborador(models.TextChoices):
    COLAB_SECADOR = 'Colaborador secador', 'Colaborador secador'
    COLAB_ALGODOEIRA = 'Colaborador algodoeira', 'Colaborador algodoeira'
    TERC_ALGODOEIRA = 'Terceirizado algodoeira', 'Terceirizado algodoeira'
    SAFRISTA_ALGODOEIRA = 'Safrista algodoeira', 'Safrista algodoeira'
    CORPORATIVO = 'Corporativo', 'Corporativo'
    # Sede / Comuns
    COLAB_SEDE = 'Colaborador sede', 'Colaborador sede'
    CORPORATIVO_SEDE = 'Corporativo sede', 'Corporativo sede'
    TERCEIROS_FAZENDA = 'Terceiros Fazenda', 'Terceiros Fazenda'

class RegistroRefeicao(models.Model):
    data_consumo = models.DateField("Data Consumo", default=timezone.now)

    local = models.CharField(
        max_length=50,
        choices=LocalRefeicao.choices,
        default=LocalRefeicao.SEDE,
        verbose_name='Cantina'
    )


    setor = models.CharField(
        max_length=100,
        choices=SetorColaborador.choices,
        verbose_name='Setor/Categoria'
    )

    qtd_cafe = models.PositiveIntegerField("Qtd. Café", default=0)
    qtd_almoco_buffet = models.PositiveIntegerField("Qtd. Buffet", default=0)
    qtd_almoco_marmita = models.PositiveIntegerField("Qtd. Marmita", default=0)
    qtd_janta = models.PositiveIntegerField("Qtd. Janta", default=0)
    qtd_lanche = models.PositiveIntegerField("Qtd. Lanche", default=0)

    valor_cafe = models.DecimalField(max_digits=8, decimal_places=2, editable=False)
    valor_almoco = models.DecimalField(max_digits=8, decimal_places=2, editable=False)
    valor_almoco_marmita = models.DecimalField(max_digits=8, decimal_places=2, editable=False)
    valor_janta = models.DecimalField(max_digits=8, decimal_places=2, editable=False)
    valor_lanche = models.DecimalField(max_digits=8, decimal_places=2, editable=False)

    valor_total = models.DecimalField("Total Gasto", max_digits=10, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Registro de Refeição"
        verbose_name_plural = "Registros de Refeições"
        ordering = ('-data_consumo', '-id')

    def save(self, *args, **kwargs):
        if not self.pk:
            tabela_atual = TabelaPreco.objects.first()
            if not tabela_atual:
                tabela_atual = TabelaPreco.objects.create()

            self.valor_cafe = tabela_atual.cafe
            self.valor_almoco = tabela_atual.buffet
            self.valor_almoco_marmita = tabela_atual.marmita
            self.valor_janta = tabela_atual.janta
            self.valor_lanche = tabela_atual.lanche

        total_cafe = Decimal(self.qtd_cafe) * self.valor_cafe
        total_buffet = Decimal(self.qtd_almoco_buffet) * self.valor_almoco
        total_marmita = Decimal(self.qtd_almoco_marmita) * self.valor_almoco_marmita
        total_janta = Decimal(self.qtd_janta) * self.valor_janta
        total_lanche = Decimal(self.qtd_lanche) * self.valor_lanche

        self.valor_total = total_cafe + total_buffet + total_marmita + total_janta + total_lanche

        super().save(*args, **kwargs)

    def data_formatada(self):
        return self.data_consumo.strftime('%d/%m/%Y')

    def __str__(self):
        return f"{self.data_formatada()} - {self.get_local_display()} - {self.get_setor_display()}"