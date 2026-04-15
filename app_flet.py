import flet as ft
from datetime import datetime
import requests
import logging
from app_config import (
    API_REFEICOES_ENDPOINT, REQUEST_TIMEOUT, PRECOS_PADRAO,
    SETORES_SECADOR, SETORES_SEDE, LOCAIS_REFEICAO,
    WINDOW_WIDTH, WINDOW_HEIGHT, THEME_MODE, BGCOLOR, PADDING,
    LOG_FILE, LOG_LEVEL
)

# ===== CONFIGURAÇÃO DE LOGS =====
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

def formatar_valor(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def salvar_refeicao_no_banco(dados: dict) -> tuple[bool, str]:
    try:
        payload = {
            'data_consumo': datetime.now().date().isoformat(),
            'local': 'SECADOR' if dados['local'] == LOCAIS_REFEICAO['SECADOR'] else 'SEDE',
            'setor': dados['setor'],
            'qtd_cafe': int(dados['qtd_cafe']),
            'qtd_almoco_buffet': int(dados['qtd_buffet']),
            'qtd_almoco_marmita': int(dados['qtd_marmita']),
            'qtd_janta': int(dados['qtd_janta']),
            'valor_cafe': PRECOS_PADRAO['cafe'],
            'valor_almoco': PRECOS_PADRAO['buffet'],
            'valor_almoco_marmita': PRECOS_PADRAO['marmita'],
            'valor_janta': PRECOS_PADRAO['janta'],
        }
        response = requests.post(API_REFEICOES_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)
        if response.status_code in [200, 201]:
            return True, f"Salvo! ID: {response.json().get('id', 'N/A')}"
        return False, "Erro na API."
    except Exception as e:
        return False, str(e)


def main(page: ft.Page):
    page.title = "Sistema de Controle de Refeições - RH"
    page.theme_mode = ft.ThemeMode.DARK if THEME_MODE == "DARK" else ft.ThemeMode.LIGHT
    page.bgcolor = BGCOLOR
    page.padding = 30
    page.window_width = WINDOW_WIDTH
    page.window_height = WINDOW_HEIGHT
    
    # ÚNICA REGRA DE ROLAGEM: A página inteira rola. Zero ListView ou Columns complexas.
    page.scroll = ft.ScrollMode.AUTO

    # --- COMPONENTES ---
    txt_total = ft.Text("R$ 0,00", size=40, color="#4a90e2", weight="bold")
    txt_setor_selecionado = ft.Text("Nenhum", size=14)

    qtd_cafe = ft.TextField(value="0", width=80, text_align="center")
    qtd_buffet = ft.TextField(value="0", width=80, text_align="center")
    qtd_marmita = ft.TextField(value="0", width=80, text_align="center")
    qtd_janta = ft.TextField(value="0", width=80, text_align="center")

    drop_local = ft.Dropdown(
        label="Local da Refeição", width=300,
        options=[
            ft.dropdown.Option(LOCAIS_REFEICAO['SECADOR']),
            ft.dropdown.Option(LOCAIS_REFEICAO['SEDE'])
        ]
    )

    drop_setor = ft.Dropdown(
        label="Setor do Colaborador", width=300,
        options=[ft.dropdown.Option("Selecione a cantina...")]
    )

    # --- FUNÇÕES ---
    def atualizar_financeiro(e):
        try:
            t = (float(qtd_cafe.value or 0) * PRECOS_PADRAO['cafe']) + \
                (float(qtd_buffet.value or 0) * PRECOS_PADRAO['buffet']) + \
                (float(qtd_marmita.value or 0) * PRECOS_PADRAO['marmita']) + \
                (float(qtd_janta.value or 0) * PRECOS_PADRAO['janta'])
            txt_total.value = formatar_valor(t)
            page.update()
        except: pass

    def ao_mudar_setor(e):
        txt_setor_selecionado.value = drop_setor.value
        page.update()

    def ao_mudar_cantina(e):
        # Atualização crua e direta. Sem clear(), sem append(). Substituição direta da lista.
        escolha = drop_local.value
        if escolha == LOCAIS_REFEICAO['SECADOR']:
            drop_setor.options = [ft.dropdown.Option(s) for s in SETORES_SECADOR]
        elif escolha == LOCAIS_REFEICAO['SEDE']:
            drop_setor.options = [ft.dropdown.Option(s) for s in SETORES_SEDE]
        
        drop_setor.value = None
        txt_setor_selecionado.value = "Aguardando..."
        page.update()

    def salvar_dados(e):
        if not drop_local.value or not drop_setor.value:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Preencha Local e Setor!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        dados = {
            'local': drop_local.value, 'setor': drop_setor.value,
            'qtd_cafe': qtd_cafe.value, 'qtd_buffet': qtd_buffet.value,
            'qtd_marmita': qtd_marmita.value, 'qtd_janta': qtd_janta.value
        }

        sucesso, msg = salvar_refeicao_no_banco(dados)

        if sucesso:
            qtd_cafe.value = "0"
            qtd_buffet.value = "0"
            qtd_marmita.value = "0"
            qtd_janta.value = "0"
            drop_local.value = None
            drop_setor.options = [ft.dropdown.Option("Selecione a cantina...")]
            drop_setor.value = None
            txt_total.value = "R$ 0,00"
            txt_setor_selecionado.value = "Nenhum"
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ {msg}"), bgcolor="green")
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"⚠️ {msg}"), bgcolor="orange")

        page.snack_bar.open = True
        page.update()

    # --- LIGAÇÕES ---
    drop_local.on_change = ao_mudar_cantina
    drop_setor.on_change = ao_mudar_setor
    for campo in [qtd_cafe, qtd_buffet, qtd_marmita, qtd_janta]:
        campo.on_change = atualizar_financeiro

    # --- LAYOUT SUPER SIMPLIFICADO ---
    def criar_card(icone, titulo, preco_key, campo):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, color="#4a90e2", size=30),
                ft.Text(titulo, size=18, weight="bold", expand=True),
                ft.Text(formatar_valor(PRECOS_PADRAO.get(preco_key, 0)), color="#4a90e2", weight="bold"),
                campo
            ]),
            bgcolor="#1e2128", padding=20, border_radius=12, margin=ft.Margin(0, 0, 0, 10)
        )

    # Sem expansões forçadas, sem listas mágicas. Só o layout limpo.
    col_esquerda = ft.Column([
        ft.Text("Configuração", size=25, weight="bold"),
        ft.Row([drop_local, drop_setor]),
        ft.Divider(height=20, color="transparent"),
        ft.Text("Lançamentos", size=25, weight="bold"),
        criar_card("coffee", "Café da Manhã", "cafe", qtd_cafe),
        criar_card("restaurant", "Almoço Buffet", "buffet", qtd_buffet),
        criar_card("lunch_dining", "Almoço Marmita", "marmita", qtd_marmita),
        criar_card("bedtime", "Janta", "janta", qtd_janta),
    ], width=650) # Largura fixa para não quebrar

    col_direita = ft.Container(
        content=ft.Column([
            ft.Text("RESUMO FINANCEIRO", weight="bold"),
            ft.Divider(color="white10"),
            txt_total,
            ft.Divider(color="white10"),
            ft.Row([ft.Text("Setor:"), txt_setor_selecionado], alignment="spaceBetween"),
            ft.Row([ft.Text("Data:"), ft.Text(datetime.now().strftime("%d/%m/%Y"), weight="bold")], alignment="spaceBetween"),
            ft.Divider(height=30, color="transparent"),
            ft.FilledButton("SALVAR NO BANCO", on_click=salvar_dados, height=50, width=300)
        ], horizontal_alignment="center"),
        bgcolor="#1e2128", padding=30, border_radius=20, width=350
    )

    page.add(
        ft.Row(
            [col_esquerda, col_direita], 
            vertical_alignment="start", 
            alignment="start"
        )
    )

if __name__ == "__main__":
    ft.run(main)