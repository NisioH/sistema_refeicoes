from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistroRefeicaoForm
from .models import RegistroRefeicao
from django.core.paginator import Paginator


def painel_refeicoes(request):
    registros = RegistroRefeicao.objects.all().order_by('-data_consumo', '-id') 

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    local_busca = request.GET.get('local')
    setor_busca = request.GET.get('setor')

    if data_inicio:
        registros = registros.filter(data_consumo__gte=data_inicio)  
    if data_fim:
        registros = registros.filter(data_consumo__lte=data_fim)  
    if local_busca:
        registros = registros.filter(local=local_busca)
    if setor_busca:
        registros = registros.filter(setor__icontains=setor_busca)  

    soma = registros.aggregate(Sum('valor_total'))['valor_total__sum']
    total_gasto = soma if soma else 0.00  

    paginator = Paginator(registros, 7) 
    numero_pagina = request.GET.get('page') 
    page_obj = paginator.get_page(numero_pagina)

    contexto = {
        'page_obj': page_obj,
        'total_gasto': total_gasto,
        'filtros': request.GET  
    }
    return render(request, 'refeicoes/painel.html', contexto)

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

