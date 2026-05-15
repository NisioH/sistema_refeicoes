import pandas as pd
from django.http import HttpResponse
from .models import RegistroRefeicao
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from collections import defaultdict
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from .models import RegistroRefeicao, TabelaPreco
from .forms import RegistroRefeicaoForm, TabelaPrecoForm
from datetime import date


def painel_refeicoes(request):
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

    if data_inicio and data_fim:
        registros = registros.filter(data_consumo__range=[data_inicio, data_fim])
    else:
        hoje = date.today()
        registros = registros.filter(
            data_consumo__year=hoje.year,
            data_consumo__month=hoje.month
        )

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
        # Criamos uma lista temporária para agrupar tudo deste setor
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
            # Impede que a tabela se quebre no meio de uma linha
            ('NOSPLIT', (0, 0), (-1, -1)),
        ])

        tabela = Table(dados_tabela, colWidths=[70, 180, 50, 50, 50, 50, 50, 90])
        tabela.setStyle(estilo_tabela_minimalista)

        bloco_setor.append(tabela)

        texto_subtotal = f"Subtotal do Setor: R$ {total_deste_setor:,.2f}".replace(',', 'X').replace('.', ',').replace(
            'X', '.')
        bloco_setor.append(Spacer(1, 5))
        bloco_setor.append(Paragraph(texto_subtotal, estilo_total_setor))

        # O KeepTogether força o ReportLab a manter o Nome do Setor + Tabela + Subtotal na mesma página
        # Se não couber no fim da página, ele joga o bloco inteiro para a próxima
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

    # Nome do arquivo ajustado para não confundir
    nome_arquivo = f"Relatorio_Refeicoes_{hoje.strftime('%m_%Y') if 'hoje' in locals() else 'Filtro'}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)

def exportr_refeicoes_excel(request):
    queryset = RegistroRefeicao.objects.all().values(
        'data_consumo', 'local', 'setor', 'qtd_cafe',
        'qtd_almoco_buffet', 'qtd_almoco_marmita', 'qtd_janta', 'qtd_lanche'
    )

    df = pd.DataFrame(list(queryset))

    df.columns = [
        'Data', 'Local', 'Setor', 'Café', 'Almoço Buffet',
        'Almoço Marmita', 'Janta', 'Lanche'
    ]

    # Cria o arquivo na memória
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Relatorio_Refeicoes.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lançamentos')

    return response


def configurar_precos(request):
    # Pega a tabela de preços existente ou cria uma nova com os valores padrão se for a primeira vez
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
