from django.shortcuts import render, redirect
from .forms import RegistroRefeicaoForm
from .models import RegistroRefeicao


def painel_refeicoes(request):
    registros = RegistroRefeicao.objects.all()

    return render(request, 'refeicoes/painel.html', {'registros': registros})

def novo_registro(request):
    if request.method == "POST":
        form = RegistroRefeicaoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('painel_refeicoes')
    else:
        form = RegistroRefeicaoForm()
   
    return render(request, 'refeicoes/novo_registro.html', {'form': form})

