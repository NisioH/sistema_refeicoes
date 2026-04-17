from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistroRefeicaoForm
from .models import RegistroRefeicao


def painel_refeicoes(request):
    # Começa pegando tudo
    registros = RegistroRefeicao.objects.all()

    # 1. Pegando os valores que o usuário digitou na barra de pesquisa (URL)
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    local_busca = request.GET.get('local')
    setor_busca = request.GET.get('setor')

    # 2. Aplicando os filtros "se" o usuário digitou algo
    if data_inicio:
        registros = registros.filter(data_consumo__gte=data_inicio)  # gte = maior ou igual
    if data_fim:
        registros = registros.filter(data_consumo__lte=data_fim)  # lte = menor ou igual
    if local_busca:
        registros = registros.filter(local=local_busca)
    if setor_busca:
        registros = registros.filter(setor__icontains=setor_busca)  # icontains = que contenha a palavra

    # 3. Calculando o Total Gasto APENAS dos itens filtrados
    soma = registros.aggregate(Sum('valor_total'))['valor_total__sum']
    total_gasto = soma if soma else 0.00  # Se não tiver nada, retorna 0

    contexto = {
        'registros': registros,
        'total_gasto': total_gasto,
        'filtros': request.GET  # Devolvemos isso para os campos não apagarem o que foi digitado!
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

