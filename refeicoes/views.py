from django.shortcuts import render
from .models import RegistroRefeicao

def painel_refeicoes(request):
    registros = RegistroRefeicao.objects.all()

    contexto = {
        'registros': registros,
    }
    return render(request, 'refeicoes/painel.html', contexto)
