import flet as ft
from datetime import datetime


def main(page: ft.Page):
    # --- CONFIGURAÇÕES DA PÁGINA ---
    page.title = "Sistema de Controle de Refeições - RH"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f1116"
    page.padding = 30
    page.window_width = 1100
    page.window_height = 850

    # --- COMPONENTES DE TEXTO (RESUMO) ---
    txt_total = ft.Text("R$ 0,00", size=40, color="#4a90e2", weight=ft.FontWeight.BOLD)
    txt_setor_selecionado = ft.Text("Nenhum", size=14, weight=ft.FontWeight.W_500)

    # --- INPUTS DE QUANTIDADE ---
    qtd_cafe = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)
    qtd_buffet = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)
    qtd_marmita = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)
    qtd_janta = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)

    # --- A TÁTICA INFALÍVEL: DROPDOWNS PRÉ-MONTADOS ---
    # Criamos as "cascas" vazias primeiro para evitar o TypeError do Flet
    drop_local = ft.Dropdown(
        label="Local da Refeição",
        width=300,
        options=[ft.dropdown.Option("Cantina do Secador"), ft.dropdown.Option("Cantina Sede")]
    )

    # 1. O Vazio (Nasce VISÍVEL e ACORDADO - sem 'disabled')
    drop_setor_vazio = ft.Dropdown(
        label="Setor do Colaborador",
        width=300,
        options=[ft.dropdown.Option("Aguardando cantina...")],
        visible=True
    )

    # 2. O do Secador (Nasce INVISÍVEL)
    drop_setor_secador = ft.Dropdown(
        label="Setor do Colaborador",
        width=300,
        visible=False,
        options=[ft.dropdown.Option(s) for s in [
            "Colaborador secador", "Colaborador algodoeira",
            "Terceirizado algodoeira", "Safrista algodoeira",
            "Corporativo", "Terceiros Fazenda"
        ]]
    )

    # 3. O da Sede (Nasce INVISÍVEL)
    drop_setor_sede = ft.Dropdown(
        label="Setor do Colaborador",
        width=300,
        visible=False,
        options=[ft.dropdown.Option(s) for s in [
            "Colaborador sede", "Corporativo", "Terceiros Fazenda"
        ]]
    )

    # Agrupamos todos no mesmo local. Como só um fica visível por vez, o layout não quebra.
    container_setores = ft.Row([drop_setor_vazio, drop_setor_secador, drop_setor_sede])

    # --- FUNÇÕES DE LÓGICA ---
    def atualizar_financeiro(e):
        try:
            t = (float(qtd_cafe.value or 0) * 9.0) + (float(qtd_buffet.value or 0) * 24.0) + \
                (float(qtd_marmita.value or 0) * 21.5) + (float(qtd_janta.value or 0) * 21.5)
            txt_total.value = f"R$ {t:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            page.update()
        except:
            pass

    def ao_mudar_cantina(e):
        escolha = drop_local.value

        # Limpa as seleções antigas antes de esconder
        drop_setor_secador.value = None
        drop_setor_sede.value = None
        txt_setor_selecionado.value = "Aguardando..."

        # Mágica da Visibilidade: Esconde os errados e mostra o certo
        if escolha == "Cantina do Secador":
            drop_setor_vazio.visible = False
            drop_setor_sede.visible = False
            drop_setor_secador.visible = True
        elif escolha == "Cantina Sede":
            drop_setor_vazio.visible = False
            drop_setor_secador.visible = False
            drop_setor_sede.visible = True

        page.update()

    def ao_mudar_setor(e):
        txt_setor_selecionado.value = e.control.value
        page.update()

    def salvar_dados(e):
        # Descobre qual Dropdown está ativo na tela para pegar o valor correto
        setor_ativo = None
        if drop_setor_secador.visible:
            setor_ativo = drop_setor_secador.value
        elif drop_setor_sede.visible:
            setor_ativo = drop_setor_sede.value

        # Validação de segurança
        if not drop_local.value or not setor_ativo:
            page.snack_bar = ft.SnackBar(ft.Text("Erro: Selecione Local e Setor antes de salvar!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        # Simulação do Envio para Banco/API
        print(f"LANÇAMENTO SALVO: Local: {drop_local.value} | Setor: {setor_ativo} | Total: {txt_total.value}")

        # --- LIMPEZA PÓS-SALVAMENTO ---
        qtd_cafe.value = "0"
        qtd_buffet.value = "0"
        qtd_marmita.value = "0"
        qtd_janta.value = "0"
        drop_local.value = None

        # Volta a visibilidade para o estado inicial (Apenas o Vazio aparece)
        drop_setor_secador.visible = False
        drop_setor_sede.visible = False
        drop_setor_vazio.visible = True

        # Limpa as seleções internas
        drop_setor_secador.value = None
        drop_setor_sede.value = None
        drop_setor_vazio.value = None

        txt_total.value = "R$ 0,00"
        txt_setor_selecionado.value = "Nenhum"

        # Alerta de Sucesso
        page.snack_bar = ft.SnackBar(ft.Text("Lançamento salvo e painel resetado com sucesso!"), bgcolor="green")
        page.snack_bar.open = True
        page.update()

    # --- LIGAÇÕES DE EVENTO (Obrigatório ser por fora) ---
    drop_local.on_change = ao_mudar_cantina
    drop_setor_secador.on_change = ao_mudar_setor
    drop_setor_sede.on_change = ao_mudar_setor
    qtd_cafe.on_change = atualizar_financeiro
    qtd_buffet.on_change = atualizar_financeiro
    qtd_marmita.on_change = atualizar_financeiro
    qtd_janta.on_change = atualizar_financeiro

    # --- LAYOUT / INTERFACE ---
    def criar_card(icone, titulo, preco, campo):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, color="#4a90e2", size=30),
                ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, expand=True),
                ft.Text(f"R$ {preco:,.2f}".replace(".", ","), color="#4a90e2", weight=ft.FontWeight.BOLD),
                campo
            ]),
            bgcolor="#1e2128", padding=20, border_radius=12, margin=ft.Margin(0, 0, 0, 10)
        )

    col_esquerda = ft.Column([
        ft.Text("Configuração", size=25, weight=ft.FontWeight.BOLD),
        ft.Row([drop_local, container_setores]),  # O Container que alterna os dropdowns entra aqui
        ft.Divider(height=20, color="transparent"),
        ft.Text("Lançamentos", size=25, weight=ft.FontWeight.BOLD),
        criar_card("coffee", "Café da Manhã", 9.00, qtd_cafe),
        criar_card("restaurant", "Almoço Buffet", 24.00, qtd_buffet),
        criar_card("lunch_dining", "Almoço Marmita", 21.50, qtd_marmita),
        criar_card("bedtime", "Janta", 21.50, qtd_janta),
    ], expand=True, scroll=ft.ScrollMode.ADAPTIVE)

    col_direita = ft.Container(
        content=ft.Column([
            ft.Text("RESUMO FINANCEIRO", weight=ft.FontWeight.BOLD),
            ft.Divider(color="white10"),
            txt_total,
            ft.Text("Total Acumulado para o Dia", size=12, color="white54"),
            ft.Divider(color="white10"),
            ft.Row([ft.Text("Setor:"), txt_setor_selecionado], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([ft.Text("Data:"), ft.Text(datetime.now().strftime("%d/%m/%Y"), weight=ft.FontWeight.BOLD)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=30, color="transparent"),
            ft.FilledButton("SALVAR NO BANCO NEON", on_click=salvar_dados,
                            style=ft.ButtonStyle(bgcolor="#4a90e2", color="white"), height=50, width=300)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#1e2128", padding=30, border_radius=20, width=350
    )

    page.add(ft.Row([col_esquerda, col_direita], vertical_alignment=ft.CrossAxisAlignment.START))


if __name__ == "__main__":
    # Rodando na porta 9999 para fugir de qualquer cache de navegador
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=9999)