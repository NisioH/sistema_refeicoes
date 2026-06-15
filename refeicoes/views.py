import io
import json
from datetime import date
from collections import defaultdict
import pandas as pd
from dateutil.relativedelta import relativedelta

from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q, F
from django.core.paginator import Paginator

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from .models import RegistroRefeicao, TabelaPreco
from .forms import RegistroRefeicaoForm, TabelaPrecoForm


def painel_refeicoes(request):
    formato_clicado = request.GET.get('formato', 'filtrar')

    if formato_clicado == 'pdf':
        return exportar_pdf(request)
    elif formato_clicado == 'excel':
        return exportar_refeicoes_excel(request)

    registros = RegistroRefeicao.objects.all().order_by('-data_consumo', '-id')

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    local_busca = request.GET.get('local')
    setor_busca = request.GET.get('setor')

    # A página inicial MANTÉM a trava do mês atual por padrão
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


def dashboard_refeicoes(request):
    # Puxa absolutamente tudo do banco para o Dashboard
    registros = RegistroRefeicao.objects.all()
    hoje = date.today()

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    # AGORA SEM RESTRIÇÃO: Se não houver filtro de data, ele calcula TODO o período histórico
    if data_inicio:
        registros = registros.filter(data_consumo__gte=data_inicio)
    if data_fim:
        registros = registros.filter(data_consumo__lte=data_fim)

    # 1. Agregações para os Cards Superiores (refletindo todo o período ou o filtro)
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

    # 2. Gráfico Acumulado (Soma real de todo o histórico/período filtrado)
    total_colab_periodo = registros.filter(
        setor__icontains='Colaborador'
    ).aggregate(total=Sum('valor_total'))['total'] or 0

    total_terc_periodo = registros.filter(
        Q(setor__icontains='Terceirizado') | Q(setor='Terceiros Fazenda')
    ).aggregate(total=Sum('valor_total'))['total'] or 0

    # 3. Gráfico de Evolução dos Últimos 3 Meses (Janela fixa comparativa)
    meses_labels = []
    dados_colaboradores = []
    dados_terceirizados = []

    for i in range(2, -1, -1):
        mes_alvo = hoje - relativedelta(months=i)
        meses_labels.append(mes_alvo.strftime('%m/%Y'))

        refeicoes_mes = RegistroRefeicao.objects.filter(
            data_consumo__month=mes_alvo.month,
            data_consumo__year=mes_alvo.year
        )

        total_colab = refeicoes_mes.filter(
            setor__icontains='Colaborador'
        ).aggregate(total=Sum('valor_total'))['total'] or 0

        total_terc = refeicoes_mes.filter(
            Q(setor__icontains='Terceirizado') | Q(setor='Terceiros Fazenda')
        ).aggregate(total=Sum('valor_total'))['total'] or 0

        dados_colaboradores.append(float(total_colab))
        dados_terceirizados.append(float(total_terc))

        # NOVO: Detalhamento financeiro em Reais para cada tipo de refeição
    detalhes = registros.aggregate(
        v_cafe=Sum(F('qtd_cafe') * F('valor_cafe')),
        v_buffet=Sum(F('qtd_almoco_buffet') * F('valor_almoco')),
        v_marmita=Sum(F('qtd_almoco_marmita') * F('valor_almoco_marmita')),
        v_janta=Sum(F('qtd_janta') * F('valor_janta')),
        v_lanche=Sum(F('qtd_lanche') * F('valor_lanche'))
    )

    contexto = {
        'total_gasto': total_gasto,
        'total_refeicoes': total_refeicoes,
        'total_buffet': total_buffet,
        'total_janta': total_janta,

        # Valores acumulados de todo o período
        'total_colab_periodo': float(total_colab_periodo),
        'total_terc_periodo': float(total_terc_periodo),

        # Listas dos 3 meses de evolução
        'meses_labels': json.dumps(meses_labels),
        'dados_colaboradores': json.dumps(dados_colaboradores),
        'dados_terceirizados': json.dumps(dados_terceirizados),

        # --- INÍCIO DOS DADOS DA NOVA FAIXA DE DETALHES ---
        'det_q_cafe': soma_total['cafe'] or 0,
        'det_v_cafe': float(detalhes['v_cafe'] or 0),
        'det_q_buffet': soma_total['buffet'] or 0,
        'det_v_buffet': float(detalhes['v_buffet'] or 0),
        'det_q_marmita': soma_total['marmita'] or 0,
        'det_v_marmita': float(detalhes['v_marmita'] or 0),
        'det_q_janta': soma_total['janta'] or 0,
        'det_v_janta': float(detalhes['v_janta'] or 0),
        'det_q_lanche': soma_total['lanche'] or 0,
        'det_v_lanche': float(detalhes['v_lanche'] or 0),

        'filtros': request.GET

    }
    return render(request, 'refeicoes/dashboard.html', contexto)


def novo_registro(request):
    if request.method == "POST":
        form = RegistroRefeicaoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('painel')
    else:
        form = RegistroRefeicaoForm()
    return render(request, 'refeicoes/novo_registro.html', {'form': form})


def editar_registro(request, id):
    registro = get_object_or_404(RegistroRefeicao, id=id)
    if request.method == 'POST':
        form = RegistroRefeicaoForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            return redirect('painel')
    else:
        form = RegistroRefeicaoForm(instance=registro)
    return render(request, 'refeicoes/novo_registro.html', {'form': form, 'registro': registro})


def excluir_registro(request, id):
    registro = get_object_or_404(RegistroRefeicao, id=id)
    registro.delete()
    return redirect('painel')


def exportar_pdf(request):
    registros = RegistroRefeicao.objects.all().order_by('setor', '-data_consumo')

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

    estilo_titulo = ParagraphStyle('TituloModerno', parent=estilos['Heading1'], alignment=TA_CENTER, fontSize=20,
                                   textColor=colors.black, spaceAfter=5, fontName='Helvetica-Bold')
    estilo_subtitulo = ParagraphStyle('Subtitulo', parent=estilos['Normal'], alignment=TA_CENTER, fontSize=11,
                                      textColor=colors.black, spaceAfter=25)
    estilo_nome_setor = ParagraphStyle('NomeSetor', parent=estilos['Heading2'], fontSize=14, textColor=colors.black,
                                       spaceBefore=10, spaceAfter=10, fontName='Helvetica-Bold')
    estilo_total_setor = ParagraphStyle('TotalSetor', parent=estilos['Normal'], alignment=TA_RIGHT, fontSize=11,
                                        fontName='Helvetica-Bold', textColor=colors.black, spaceTop=5)

    elementos.append(Paragraph("Relatório de Refeições", estilo_titulo))
    elementos.append(Paragraph("Extrato analítico gerado pelo sistema.", estilo_subtitulo))

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

    elementos.append(Spacer(1, 10))
    estilo_total_geral = ParagraphStyle('TotalGeral', parent=estilos['Heading2'], alignment=TA_RIGHT,
                                        textColor=colors.black, spaceTop=10, fontName='Helvetica-Bold', fontSize=14)
    texto_total_geral = f"CUSTO TOTAL DO PERÍODO: R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace(
        'X', '.')
    elementos.append(Paragraph(texto_total_geral, estilo_total_geral))

    doc.build(elementos)
    buffer.seek(0)

    hoje = date.today()
    nome_arquivo = f"Relatorio_Refeicoes_{hoje.strftime('%m_%Y') if 'hoje' in locals() else 'Filtro'}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)


def exportar_refeicoes_excel(request):
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

    queryset = registros.values(
        'data_consumo', 'local', 'setor', 'qtd_cafe',
        'qtd_almoco_buffet', 'qtd_almoco_marmita', 'qtd_janta', 'qtd_lanche', 'valor_total'
    )

    df = pd.DataFrame(list(queryset))

    if not df.empty:
        df.columns = ['Data', 'Local', 'Setor', 'Café', 'Almoço Buffet', 'Almoço Marmita', 'Janta', 'Lanche',
                      'Valor Total']
        df['Data'] = pd.to_datetime(df['Data']).dt.date
    else:
        df = pd.DataFrame(
            columns=['Data', 'Local', 'Setor', 'Café', 'Almoço Buffet', 'Almoço Marmita', 'Janta', 'Lanche',
                     'Valor Total'])

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
            return redirect('painel')
    else:
        form = TabelaPrecoForm(instance=tabela)

    return render(request, 'refeicoes/configurar_precos.html', {'form': form, 'tabela': tabela})