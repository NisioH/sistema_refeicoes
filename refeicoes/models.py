from django.db import models

class LocalRefeicao(models.TextChoices):
    SEDE = 'SEDE', 'Cantina da Sede'
    SECADOR = 'SECADOR', 'Cantina do Secador'

class RegistroRefeicao(models.Model):
    data_consumo = models.DateField(verbose_name='Data Consumo')

    local = models.CharField(
        max_length=50,
        choices=LocalRefeicao.choices,
        default=LocalRefeicao.SEDE,
    )

    setor = models.IntegerField(max_length=100, null=True, blank=True, verbose_name='Setor/Categoria')

    qtd_cafe = models.IntegerField(default=0)
    qtd_almoco_buffet = models.IntegerField(default=0)
    qtd_almoco_marmita = models.IntegerField(default=0)
    qtd_janta = models.IntegerField(default=0)
    qtd_lanche = models.IntegerField(default=0)

    valor_cafe = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)
    valor_almoco = models.DecimalField(max_digits=5, decimal_places=2, default=24.00)
    valor_almoco_marmita = models.DecimalField(max_digits=5, decimal_places=2, default=21.50)
    valor_janta = models.DecimalField(max_digits=5, decimal_places=2, default=21.50)
    valor_lanche = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)

    def total_gasto(self):
        return (
            (self.qtd_cafe * float(self.valor_cafe)) +
            (self.qtd_almoco_buffet * float(self.valor_almoco)) +
            (self.qtd_almoco_marmita * float(self.valor_almoco_marmita)) +
            (self.qtd_janta * float(self.valor_janta)) +
            (self.qtd_lanche * float(self.valor_lanche))
        )

    def data_formatada(self):
        return self.data_consumo.strftime('%d/%m/%Y')

    def __str__(self):
        return f"{self.data_formatada()} - {self.get_local_display()} - {self.setor}"
