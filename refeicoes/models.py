from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Fazenda(models.Model):
    nome = models.CharField("Nome da Fazenda", max_length=100)

    def __str__(self):
        return self.nome


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    fazenda_lotacao = models.ForeignKey(Fazenda, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name="Fazenda do RH")
    is_dono = models.BooleanField("É Administrador? (Acesso Total)", default=False)

    def __str__(self):
        return f"{self.usuario.username} - {'Admin' if self.is_dono else 'RH'}"


class TabelaPreco(models.Model):
    fazenda = models.OneToOneField(Fazenda, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Fazenda")

    cafe = models.DecimalField("Café da Manhã", max_digits=5, decimal_places=2, default=9.00,
                               validators=[MinValueValidator(Decimal('0.00'))])
    buffet = models.DecimalField("Almoço Buffet", max_digits=5, decimal_places=2, default=24.00,
                                 validators=[MinValueValidator(Decimal('0.00'))])
    marmita = models.DecimalField("Almoço Marmita", max_digits=5, decimal_places=2, default=21.50,
                                  validators=[MinValueValidator(Decimal('0.00'))])
    janta = models.DecimalField("Janta", max_digits=5, decimal_places=2, default=21.50,
                                validators=[MinValueValidator(Decimal('0.00'))])
    lanche = models.DecimalField("Lanche", max_digits=5, decimal_places=2, default=9.00,
                                 validators=[MinValueValidator(Decimal('0.00'))])
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tabela Preço"
        verbose_name_plural = "Tabela Preços"

    def __str__(self):
        nome_fazenda = self.fazenda.nome if self.fazenda else "Matriz (Padrão)"
        return f"Preços vigentes - {nome_fazenda} (Atualizado em {self.data_atualizacao.strftime('%d/%m/%Y')})"


class LocalRefeicao(models.TextChoices):
    SEDE = 'SEDE', 'Cantina da Sede'
    SECADOR = 'SECADOR', 'Cantina do Secador'
    CANTINA_MATAO = 'CANTINA_MATAO', 'Cantina Matão'
    CANTINA_BC = 'CANTINA_BC', 'Cantina BC'
    CANTINA_LAGOA = 'CANTINA_LAGOA', 'Cantina Lagoa'


class SetorColaborador(models.TextChoices):
    COLAB_SECADOR = 'Colaborador secador', 'Colaborador Secador'
    COLAB_ALGODOEIRA = 'Colaborador algodoeira', 'Colaborador Algodoeira'
    COLAB_ESCRITORIO = 'Colaborador escritorio', 'Colaborador Escritório'
    TERC_ALGODOEIRA = 'Terceirizado algodoeira', 'Terceirizado Algodoeira'
    SAFRISTA_ALGODOEIRA = 'Safrista algodoeira', 'Safrista Algodoeira'
    SAFRISTA_SECADOR = 'Safrista secador', 'Safrista Secador'
    CORPORATIVO = 'Corporativo', 'Corporativo'
    COLAB_SEDE = 'Colaborador Sede', 'Colaborador Sede'
    CORPORATIVO_SEDE = 'Corporativo sede', '(Não utilizar) Corporativo Sede'
    TERCEIROS_FAZENDA = 'Terceiros Fazenda', 'Terceirizado Sede'
    TERCEIROS = 'Terceiros', 'Terceiros'


class RegistroRefeicao(models.Model):
    fazenda = models.ForeignKey(Fazenda, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Fazenda")

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
            tabela_atual = None
            if self.fazenda:
                tabela_atual = TabelaPreco.objects.filter(fazenda=self.fazenda).first()

            if not tabela_atual:
                tabela_atual = TabelaPreco.objects.filter(fazenda__isnull=True).first()

            if not tabela_atual:
                tabela_atual = TabelaPreco.objects.create(fazenda=self.fazenda)

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
