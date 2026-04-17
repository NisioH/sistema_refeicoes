from django.shortcuts import render, redirect, get_object_or_404
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


def editar_registro(request, id):
    registro = get_object_or_404(RegistroRefeicao, id=id)

    if request.method == 'POST':
        form = RegistroRefeicaoForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            return redirect('painel_refeicoes')
    else:
        form = RegistroRefeicaoForm(instance=registro)

    contexto = {'form': form, 'registro': registro}
    return render(request, 'refeicoes/novo_registro.html', contexto)

def excluir_registro(request, id):
    registro = get_object_or_404(RegistroRefeicao, id=id)
    registro.delete()
    return redirect('painel_refeicoes')

