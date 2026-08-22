from django.contrib import admin
from .models import RegistroRefeicao, TabelaPreco, Fazenda, Perfil

# Isso avisa o painel do Django para exibir a sua tabel
from django.contrib import admin

# Register your models here.
admin.site.register(Fazenda)
admin.site.register(Perfil)

admin.site.register(TabelaPreco)
admin.site.register(RegistroRefeicao)