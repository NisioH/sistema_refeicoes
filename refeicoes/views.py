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

    # VOLTOU AO NORMAL (Sem o __nome)
    if local_busca:
        registros = registros.filter(local=local_busca)
    if setor_busca:
        registros = registros.filter(setor__icontains=setor_busca)

    soma_total = registros.aggregate(
        total=Sum('valor_total'),
        cafe=Sum('qtd_cafe'),
        buffet=Sum('qtd_almoco_buffet'),
        marmita=Sum('qtd_almoco_marmita'),
        janta=Sum('qtd_janta'),
        lanche=Sum('qtd_lanche')
    )

    detalhes = registros.aggregate(
        v_cafe=Sum(F('qtd_cafe') * F('valor_cafe')),
        v_buffet=Sum(F('qtd_almoco_buffet') * F('valor_almoco')),
        v_marmita=Sum(F('qtd_almoco_marmita') * F('valor_almoco_marmita')),
        v_janta=Sum(F('qtd_janta') * F('valor_janta')),
        v_lanche=Sum(F('qtd_lanche') * F('valor_lanche'))
    )

    # Usando o cálculo dinâmico da função F() para garantir o valor mesmo nos importados
    total_gasto = (
            (detalhes['v_cafe'] or 0) + (detalhes['v_buffet'] or 0) +
            (detalhes['v_marmita'] or 0) + (detalhes['v_janta'] or 0) + (detalhes['v_lanche'] or 0)
    )

    total_refeicoes = (
            (soma_total['cafe'] or 0) + (soma_total['buffet'] or 0) +
            (soma_total['marmita'] or 0) + (soma_total['janta'] or 0) + (soma_total['lanche'] or 0)
    )
    total_buffet = soma_total['buffet'] or 0
    total_janta = soma_total['janta'] or 0

    paginator = Paginator(registros, 7)
    numero_pagina = request.GET.get('page')
    page_obj = paginator.get_page(numero_pagina)

    contexto = {
        'page_obj': page_obj,
        'total_gasto': float(total_gasto),
        'total_refeicoes': total_refeicoes,
        'total_buffet': total_buffet,
        'total_janta': total_janta,

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
    return render(request, 'refeicoes/painel.html', contexto)


def dashboard_refeicoes(request):
    registros = RegistroRefeicao.objects.all()
    hoje = date.today()

    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if data_inicio:
        registros = registros.filter(data_consumo__gte=data_inicio)
    if data_fim:
        registros = registros.filter(data_consumo__lte=data_fim)

    soma_total = registros.aggregate(
        total=Sum('valor_total'),
        cafe=Sum('qtd_cafe'),
        buffet=Sum('qtd_almoco_buffet'),
        marmita=Sum('qtd_almoco_marmita'),
        janta=Sum('qtd_janta'),
        lanche=Sum('qtd_lanche')
    )

    detalhes = registros.aggregate(
        v_cafe=Sum(F('qtd_cafe') * F('valor_cafe')),
        v_buffet=Sum(F('qtd_almoco_buffet') * F('valor_almoco')),
        v_marmita=Sum(F('qtd_almoco_marmita') * F('valor_almoco_marmita')),
        v_janta=Sum(F('qtd_janta') * F('valor_janta')),
        v_lanche=Sum(F('qtd_lanche') * F('valor_lanche'))
    )

    total_gasto = (
            (detalhes['v_cafe'] or 0) + (detalhes['v_buffet'] or 0) +
            (detalhes['v_marmita'] or 0) + (detalhes['v_janta'] or 0) + (detalhes['v_lanche'] or 0)
    )

    total_refeicoes = (
            (soma_total['cafe'] or 0) + (soma_total['buffet'] or 0) +
            (soma_total['marmita'] or 0) + (soma_total['janta'] or 0) + (soma_total['lanche'] or 0)
    )
    total_buffet = soma_total['buffet'] or 0
    total_janta = soma_total['janta'] or 0

    def calc_financeiro(queryset):
        agg = queryset.aggregate(
            vc=Sum(F('qtd_cafe') * F('valor_cafe')),
            vb=Sum(F('qtd_almoco_buffet') * F('valor_almoco')),
            vm=Sum(F('qtd_almoco_marmita') * F('valor_almoco_marmita')),
            vj=Sum(F('qtd_janta') * F('valor_janta')),
            vl=Sum(F('qtd_lanche') * F('valor_lanche'))
        )
        return (agg['vc'] or 0) + (agg['vb'] or 0) + (agg['vm'] or 0) + (agg['vj'] or 0) + (agg['vl'] or 0)

    # 1. CRIAMOS A REGRA DO QUE É TERCEIRO
    filtro_terceiros = Q(setor__icontains='Terceirizado') | Q(setor='Terceiros Fazenda')

    # 2. COLABORADOR PASSA A SER TUDO QUE "NÃO É TERCEIRO" (Usando o .exclude)
    total_colab_periodo = calc_financeiro(registros.exclude(filtro_terceiros))
    total_terc_periodo = calc_financeiro(registros.filter(filtro_terceiros))

    meses_labels = []
    dados_colaboradores = []
    dados_terceirizados = []
    qtds_colaboradores = []
    qtds_terceirizados = []

    for i in range(2, -1, -1):
        mes_alvo = hoje - relativedelta(months=i)
        meses_labels.append(mes_alvo.strftime('%m/%Y'))

        refeicoes_mes = RegistroRefeicao.objects.filter(
            data_consumo__month=mes_alvo.month,
            data_consumo__year=mes_alvo.year
        )

        # APLICAMOS A MESMA LÓGICA MÊS A MÊS
        total_colab = calc_financeiro(refeicoes_mes.exclude(filtro_terceiros))
        total_terc = calc_financeiro(refeicoes_mes.filter(filtro_terceiros))

        agg_colab = refeicoes_mes.exclude(filtro_terceiros).aggregate(
            c=Sum('qtd_cafe'), b=Sum('qtd_almoco_buffet'), m=Sum('qtd_almoco_marmita'), j=Sum('qtd_janta'),
            l=Sum('qtd_lanche')
        )
        q_colab = (agg_colab['c'] or 0) + (agg_colab['b'] or 0) + (agg_colab['m'] or 0) + (agg_colab['j'] or 0) + (
                    agg_colab['l'] or 0)

        agg_terc = refeicoes_mes.filter(filtro_terceiros).aggregate(
            c=Sum('qtd_cafe'), b=Sum('qtd_almoco_buffet'), m=Sum('qtd_almoco_marmita'), j=Sum('qtd_janta'),
            l=Sum('qtd_lanche')
        )
        q_terc = (agg_terc['c'] or 0) + (agg_terc['b'] or 0) + (agg_terc['m'] or 0) + (agg_terc['j'] or 0) + (
                    agg_terc['l'] or 0)

        dados_colaboradores.append(float(total_colab))
        dados_terceirizados.append(float(total_terc))
        qtds_colaboradores.append(q_colab)
        qtds_terceirizados.append(q_terc)

    contexto = {
        'total_gasto': float(total_gasto),
        'total_refeicoes': total_refeicoes,
        'total_buffet': total_buffet,
        'total_janta': total_janta,

        # ---> AGORA AS VARIÁVEIS ESTÃO INDO PARA O DASHBOARD <---
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
        # --------------------------------------------------------

        'total_colab_periodo': float(total_colab_periodo),
        'total_terc_periodo': float(total_terc_periodo),
        'meses_labels': json.dumps(meses_labels),
        'dados_colaboradores': json.dumps(dados_colaboradores),
        'dados_terceirizados': json.dumps(dados_terceirizados),
        'qtds_colaboradores': json.dumps(qtds_colaboradores),
        'qtds_terceirizados': json.dumps(qtds_terceirizados),
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

    # VOLTOU AO NORMAL
    if local_busca: registros = registros.filter(local=local_busca)
    if setor_busca: registros = registros.filter(setor__icontains=setor_busca)

    dados_por_setor = defaultdict(list)
    total_geral = 0

    for r in registros:
        # VOLTOU AO NORMAL (Lendo como display para evitar erro no ReportLab)
        dados_por_setor[r.get_setor_display() if hasattr(r, 'get_setor_display') else r.setor].append(r)

        # O PDF recalcula somando linha a linha, então podemos usar a mesma lógica
        valor_da_linha = (
                (float(r.qtd_cafe * r.valor_cafe) if r.qtd_cafe else 0) +
                (float(r.qtd_almoco_buffet * r.valor_almoco) if r.qtd_almoco_buffet else 0) +
                (float(r.qtd_almoco_marmita * r.valor_almoco_marmita) if r.qtd_almoco_marmita else 0) +
                (float(r.qtd_janta * r.valor_janta) if r.qtd_janta else 0) +
                (float(r.qtd_lanche * r.valor_lanche) if r.qtd_lanche else 0)
        )
        total_geral += valor_da_linha

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

    elementos.append(Paragraph("Relatório de Refeições", estilo_titulo))
    elementos.append(Paragraph("Extrato analítico gerado pelo sistema.", estilo_subtitulo))

    def formata_rs(valor):
        if valor and valor > 0:
            return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return '-'

    for setor_nome, lista_refeicoes in dados_por_setor.items():
        bloco_setor = []
        bloco_setor.append(Paragraph(f"Setor: {setor_nome}", estilo_nome_setor))

        cabecalho = ['Data', 'Cantina', 'Café', 'Buffet', 'Marm.', 'Janta', 'Lanche', 'Valor Total']
        dados_tabela = [cabecalho]

        total_deste_setor = 0
        v_cafe = v_buffet = v_marmita = v_janta = v_lanche = 0

        for r in lista_refeicoes:
            c_v = float(r.qtd_cafe * r.valor_cafe) if r.qtd_cafe else 0
            b_v = float(r.qtd_almoco_buffet * r.valor_almoco) if r.qtd_almoco_buffet else 0
            m_v = float(r.qtd_almoco_marmita * r.valor_almoco_marmita) if r.qtd_almoco_marmita else 0
            j_v = float(r.qtd_janta * r.valor_janta) if r.qtd_janta else 0
            l_v = float(r.qtd_lanche * r.valor_lanche) if r.qtd_lanche else 0

            v_cafe += c_v
            v_buffet += b_v
            v_marmita += m_v
            v_janta += j_v
            v_lanche += l_v

            valor_linha = c_v + b_v + m_v + j_v + l_v
            total_deste_setor += valor_linha

            # VOLTOU AO NORMAL (Lendo local_display)
            linha = [
                r.data_formatada() if hasattr(r, 'data_formatada') else r.data_consumo.strftime('%d/%m/%Y'),
                r.get_local_display() if hasattr(r, 'get_local_display') else r.local,
                r.qtd_cafe or '-',
                r.qtd_almoco_buffet or '-',
                r.qtd_almoco_marmita or '-',
                r.qtd_janta or '-',
                r.qtd_lanche or '-',
                formata_rs(valor_linha)
            ]
            dados_tabela.append(linha)

        linha_total = [
            '',
            'SUBTOTAL DO SETOR:',
            formata_rs(v_cafe),
            formata_rs(v_buffet),
            formata_rs(v_marmita),
            formata_rs(v_janta),
            formata_rs(v_lanche),
            formata_rs(total_deste_setor)
        ]
        dados_tabela.append(linha_total)

        # Removemos o ('NOSPLIT', (0, 0), (-1, -1)) daqui de dentro
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
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -1), (-2, -1), 9),
        ])

        # Adicionamos o repeatRows=1 para repetir o cabeçalho se a tabela quebrar de página
        tabela = Table(dados_tabela, colWidths=[70, 160, 65, 65, 65, 65, 65, 90], repeatRows=1)
        tabela.setStyle(estilo_tabela_minimalista)

        # Removemos o KeepTogether e adicionamos os itens diretamente aos elementos do PDF
        elementos.append(Paragraph(f"Setor: {setor_nome}", estilo_nome_setor))
        elementos.append(tabela)
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
    nome_arquivo = f"Relatorio_Refeicoes_{hoje.strftime('%m_%Y')}.pdf"
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

    # VOLTOU AO NORMAL
    if local_busca: registros = registros.filter(local=local_busca)
    if setor_busca: registros = registros.filter(setor__icontains=setor_busca)

    # VOLTOU AO NORMAL
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