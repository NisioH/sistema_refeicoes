import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from .models import RegistroRefeicao, TabelaPreco
from .forms import RegistroRefeicaoForm, TabelaPrecoForm

from collections import defaultdict

import json
from django.db.models import Sum
from datetime import date
from django.shortcuts import render
from django.core.paginator import Paginator

def painel_refeicoes(request):
    # 1. PEGA QUAL BOTÃO FOI CLICADO (se não for nenhum, assume 'filtrar')
    formato_clicado = request.GET.get('formato', 'filtrar')

    # Se o botão clicado foi PDF ou Excel, redireciona a chamada
    # passando os mesmos filtros para a função de exportação correspondente
    if formato_clicado == 'pdf':
        return exportar_pdf(request)
    elif formato_clicado == 'excel':
        return exportar_refeicoes_excel(request)

    # 2. SE FOI O BOTÃO FILTRAR (OU ACESSO NORMAL), SEGUE O FLUXO PADRÃO
    registros = RegistroRefeicao.objects.all().order_by('-data_consumo', '-id')

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    local_busca = request.GET.get('local')
    setor_busca = request.GET.get('setor')

    if not data_inicio and not data_fim:
        hoje = date.today()
        registros = registros.filter(
            data_consumo__year=hoje.year,
            data_consumo__month=hoje.month
        )
    else:
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





# Mantenha os seus outros imports normais lá em cima...

def dashboard_refeicoes(request):
    """Nova view focada exclusivamente nos indicadores e gráficos neon"""
    registros = RegistroRefeicao.objects.all()

    # Filtros opcionais também para o Dashboard (caso queira ver gráficos de meses específicos)
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if not data_inicio and not data_fim:
        hoje = date.today()
        registros = registros.filter(data_consumo__year=hoje.year, data_consumo__month=hoje.month)
    else:
        if data_inicio:
            registros = registros.filter(data_consumo__gte=data_inicio)
        if data_fim:
            registros = registros.filter(data_consumo__lte=data_fim)

    # 1. Agregações para os Cards Superiores
    soma_total = registros.aggregate(
        total=Sum('valor_total'),
        cafe=Sum('qtd_cafe'),
        buffet=Sum('qtd_almoco_buffet'),
        marmita=Sum('qtd_almoco_marmita'),
        janta=Sum('qtd_janta'),
        lanche=Sum('qtd_lanche')
    )

    total_gasto = float(soma_total['total'] or 0.00)
    total_refeicoes = (
            (soma_total['cafe'] or 0) + (soma_total['buffet'] or 0) +
            (soma_total['marmita'] or 0) + (soma_total['janta'] or 0) + (soma_total['lanche'] or 0)
    )
    total_buffet = soma_total['buffet'] or 0
    total_janta = soma_total['janta'] or 0

    # ===============================================================
    # 2. Dados da Pizza (Distribuição por Setor) - AGRUPANDO NOMES
    # ===============================================================
    setores_dados = registros.values('setor').annotate(total_setor=Sum('valor_total'))

    agrupamento_setores = {}
    temp_registro = RegistroRefeicao()

    for s in setores_dados:
        temp_registro.setor = s['setor']
        nome_original = temp_registro.get_setor_display()

        # Cria uma chave toda em minúsculo para unificar (ex: "colaborador sede")
        chave_padrao = nome_original.lower().strip()

        # Formata o nome para ficar bonito na legenda do gráfico (ex: "Colaborador Sede")
        # O .title() transforma "Colaborador sede" em "Colaborador Sede"
        nome_bonito = nome_original.title()

        # Se já existe essa chave no dicionário, apenas soma o valor
        if chave_padrao in agrupamento_setores:
            agrupamento_setores[chave_padrao]['valor'] += float(s['total_setor'] or 0)
        else:
            # Se for a primeira vez, cria a entrada no dicionário
            agrupamento_setores[chave_padrao] = {
                'nome': nome_bonito,
                'valor': float(s['total_setor'] or 0)
            }

    # Desempacota o dicionário unificado para as listas do gráfico
    labels_setores = [item['nome'] for item in agrupamento_setores.values()]
    valores_setores = [item['valor'] for item in agrupamento_setores.values()]

    # 3. Dados da Ocupação por Local (Sede vs Secador)
    locais_dados = registros.values('local').annotate(total_local=Sum('valor_total'))

    labels_locais = []
    valores_locais = []
    for l in locais_dados:
        temp_registro.local = l['local']
        labels_locais.append(temp_registro.get_local_display())
        valores_locais.append(float(l['total_local'] or 0))

    # Pegamos todos os registros ordenados para enviar para o HTML (para o Modal ler)
    todos_registros_filtrados = registros.order_by('-data_consumo', '-id')

    contexto = {
        'total_gasto': total_gasto,
        'total_refeicoes': total_refeicoes,
        'total_buffet': total_buffet,
        'total_janta': total_janta,
        'todos_registros': todos_registros_filtrados,

        # Passamos as listas convertidas em JSON para o JavaScript
        'setores_labels_json': json.dumps(labels_setores),
        'setores_valores_json': json.dumps(valores_setores),
        'locais_labels_json': json.dumps(labels_locais),
        'locais_valores_json': json.dumps(valores_locais),
        'filtros': request.GET
    }
    return render(request, 'refeicoes/dashboard.html', contexto)


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


def exportar_pdf(request):
    registros = RegistroRefeicao.objects.all().order_by('setor', '-data_consumo')

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # Usar __gte e __lte em vez de __range para lidar melhor com datas que só tem um dos campos preenchidos
    if not data_inicio and not data_fim:
        hoje = date.today()
        registros = registros.filter(
            data_consumo__year=hoje.year,
            data_consumo__month=hoje.month
        )
    else:
        if data_inicio:
            registros = registros.filter(data_consumo__gte=data_inicio)
        if data_fim:
            registros = registros.filter(data_consumo__lte=data_fim)

    local_busca = request.GET.get('local')
    setor_busca = request.GET.get('setor')

    if local_busca: registros = registros.filter(local=local_busca)
    if setor_busca: registros = registros.filter(setor__icontains=setor_busca)

    dados_por_setor = defaultdict(list)
    total_geral = 0

    for r in registros:
        dados_por_setor[r.get_setor_display()].append(r)
        total_geral += r.valor_total

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=40, leftMargin=40, topMargin=40,
                            bottomMargin=40)
    elementos = []

    estilos = getSampleStyleSheet()

    # --- Estilos ---
    estilo_titulo = ParagraphStyle(
        'TituloModerno', parent=estilos['Heading1'], alignment=TA_CENTER,
        fontSize=20, textColor=colors.black, spaceAfter=5, fontName='Helvetica-Bold'
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo', parent=estilos['Normal'], alignment=TA_CENTER,
        fontSize=11, textColor=colors.black, spaceAfter=25
    )
    estilo_nome_setor = ParagraphStyle(
        'NomeSetor', parent=estilos['Heading2'], fontSize=14,
        textColor=colors.black, spaceBefore=10, spaceAfter=10, fontName='Helvetica-Bold'
    )
    estilo_total_setor = ParagraphStyle(
        'TotalSetor', parent=estilos['Normal'], alignment=TA_RIGHT,
        fontSize=11, fontName='Helvetica-Bold', textColor=colors.black, spaceTop=5
    )

    elementos.append(Paragraph("Relatório de Refeições", estilo_titulo))
    elementos.append(Paragraph("Extrato analítico gerado pelo sistema.", estilo_subtitulo))

    # Loop pelos setores
    for setor, lista_refeicoes in dados_por_setor.items():
        bloco_setor = []

        bloco_setor.append(Paragraph(f"Setor: {setor}", estilo_nome_setor))

        cabecalho = ['Data', 'Cantina', 'Café', 'Buffet', 'Marm.', 'Janta', 'Lanche', 'Valor Total']
        dados_tabela = [cabecalho]

        total_deste_setor = 0
        for r in lista_refeicoes:
            linha = [
                r.data_formatada(),
                r.get_local_display(),
                r.qtd_cafe or '-',
                r.qtd_almoco_buffet or '-',
                r.qtd_almoco_marmita or '-',
                r.qtd_janta or '-',
                r.qtd_lanche or '-',
                f"R$ {r.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            ]
            dados_tabela.append(linha)
            total_deste_setor += r.valor_total

        estilo_tabela_minimalista = TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-2, -1), 'CENTER'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('LINEBELOW', (0, 0), (-1, 0), 1.2, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('NOSPLIT', (0, 0), (-1, -1)),
        ])

        tabela = Table(dados_tabela, colWidths=[70, 180, 50, 50, 50, 50, 50, 90])
        tabela.setStyle(estilo_tabela_minimalista)

        bloco_setor.append(tabela)

        texto_subtotal = f"Subtotal do Setor: R$ {total_deste_setor:,.2f}".replace(',', 'X').replace('.', ',').replace(
            'X', '.')
        bloco_setor.append(Spacer(1, 5))
        bloco_setor.append(Paragraph(texto_subtotal, estilo_total_setor))

        elementos.append(KeepTogether(bloco_setor))
        elementos.append(Spacer(1, 20))

    # Total Geral
    elementos.append(Spacer(1, 10))
    estilo_total_geral = ParagraphStyle(
        'TotalGeral', parent=estilos['Heading2'], alignment=TA_RIGHT,
        textColor=colors.black, spaceTop=10, fontName='Helvetica-Bold', fontSize=14
    )
    texto_total_geral = f"CUSTO TOTAL DO PERÍODO: R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace(
        'X', '.')
    elementos.append(Paragraph(texto_total_geral, estilo_total_geral))

    doc.build(elementos)
    buffer.seek(0)

    hoje = date.today()
    nome_arquivo = f"Relatorio_Refeicoes_{hoje.strftime('%m_%Y') if 'hoje' in locals() else 'Filtro'}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)


def exportar_refeicoes_excel(request):
    # Pega os mesmos filtros usados na visualização para o Excel sair certinho
    registros = RegistroRefeicao.objects.all()

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if not data_inicio and not data_fim:
        hoje = date.today()
        registros = registros.filter(
            data_consumo__year=hoje.year,
            data_consumo__month=hoje.month
        )
    else:
        if data_inicio:
            registros = registros.filter(data_consumo__gte=data_inicio)
        if data_fim:
            registros = registros.filter(data_consumo__lte=data_fim)

    local_busca = request.GET.get('local')
    setor_busca = request.GET.get('setor')

    if local_busca: registros = registros.filter(local=local_busca)
    if setor_busca: registros = registros.filter(setor__icontains=setor_busca)

    # Extrai só os valores necessários para a planilha
    queryset = registros.values(
        'data_consumo', 'local', 'setor', 'qtd_cafe',
        'qtd_almoco_buffet', 'qtd_almoco_marmita', 'qtd_janta', 'qtd_lanche', 'valor_total'
    )

    df = pd.DataFrame(list(queryset))

    # Se a tabela não estiver vazia, arruma os nomes das colunas
    if not df.empty:
        df.columns = [
            'Data', 'Local', 'Setor', 'Café', 'Almoço Buffet',
            'Almoço Marmita', 'Janta', 'Lanche', 'Valor Total'
        ]

        # Garante que as datas fiquem bonitas (sem horas zeradas atrapalhando) no Excel
        df['Data'] = pd.to_datetime(df['Data']).dt.date
    else:
        # Cria colunas vazias se não tiver dados para não dar erro no pandas
        df = pd.DataFrame(columns=[
            'Data', 'Local', 'Setor', 'Café', 'Almoço Buffet',
            'Almoço Marmita', 'Janta', 'Lanche', 'Valor Total'
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Relatorio_Refeicoes.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lançamentos')

    return response


def configurar_precos(request):
    tabela = TabelaPreco.objects.first()
    if not tabela:
        tabela = TabelaPreco.objects.create()

    if request.method == 'POST':
        form = TabelaPrecoForm(request.POST, instance=tabela)
        if form.is_valid():
            form.save()
            return redirect('painel_refeicoes')
    else:
        form = TabelaPrecoForm(instance=tabela)

    return render(request, 'refeicoes/configurar_precos.html', {'form': form, 'tabela': tabela})