import flet as ft
from datetime import datetime


def main(page: ft.Page):
    page.title = "Sistema de Controle de Refeições - RH"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f1116"
    page.padding = 30

    # --- COMPONENTES DE TEXTO ---
    txt_total = ft.Text("R$ 0,00", size=40, color="#4a90e2", weight=ft.FontWeight.BOLD)
    txt_setor_selecionado = ft.Text("Nenhum", size=14)

    # --- INPUTS ---
    qtd_cafe = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)
    qtd_buffet = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)
    qtd_marmita = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)
    qtd_janta = ft.TextField(value="0", width=80, text_align=ft.TextAlign.CENTER)

    # --- A TÁTICA INFALÍVEL: DROPDOWNS PRÉ-MONTADOS ---
    drop_local = ft.Dropdown(
        label="Local da Refeição",
        width=300,
        options=[ft.dropdown.Option("Cantina do Secador"), ft.dropdown.Option("Cantina Sede")]
    )

    # 1. O Vazio (Começa visível)
    drop_setor_vazio = ft.Dropdown(label="Setor do Colaborador", width=300, disabled=True, visible=True)

    # 2. O do Secador (Começa invisível)
    drop_setor_secador = ft.Dropdown(
        label="Setor do Colaborador", width=300, visible=False,
        options=[ft.dropdown.Option(s) for s in
                 ["Colaborador secador", "Colaborador algodoeira", "Terceirizado algodoeira", "Safrista algodoeira",
                  "Corporativo", "Terceiros Fazenda"]]
    )

    # 3. O da Sede (Começa invisível)
    drop_setor_sede = ft.Dropdown(
        label="Setor do Colaborador", width=300, visible=False,
        options=[ft.dropdown.Option(s) for s in ["Colaborador sede", "Corporativo", "Terceiros Fazenda"]]
    )

    # Agrupamos todos no mesmo local. Como só um fica visível por vez, o layout não quebra.
    container_setores = ft.Row([drop_setor_vazio, drop_setor_secador, drop_setor_sede])

    # --- FUNÇÕES ---
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

        # Mágica da Visibilidade
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
        # Descobre qual Dropdown está ativo para pegar o valor
        setor_ativo = None
        if drop_setor_secador.visible:
            setor_ativo = drop_setor_secador.value
        elif drop_setor_sede.visible:
            setor_ativo = drop_setor_sede.value

        if not drop_local.value or not setor_ativo:
            page.snack_bar = ft.SnackBar(ft.Text("Erro: Selecione Local e Setor!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        print(f"SALVO: {drop_local.value} | {setor_ativo} | {txt_total.value}")

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
        drop_setor_secador.value = None
        drop_setor_sede.value = None

        txt_total.value = "R$ 0,00"
        txt_setor_selecionado.value = "Nenhum"

        page.snack_bar = ft.SnackBar(ft.Text("Lançamento salvo e painel resetado!"), bgcolor="green")
        page.snack_bar.open = True
        page.update()

    # --- LIGAÇÕES DE EVENTO (SEM ERROS) ---
    drop_local.on_change = ao_mudar_cantina
    drop_setor_secador.on_change = ao_mudar_setor
    drop_setor_sede.on_change = ao_mudar_setor
    qtd_cafe.on_change = atualizar_financeiro
    qtd_buffet.on_change = atualizar_financeiro
    qtd_marmita.on_change = atualizar_financeiro
    qtd_janta.on_change = atualizar_financeiro

    # --- LAYOUT ---
    def criar_card(icone, titulo, preco, campo):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, color="#4a90e2"),
                ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, expand=True),
                ft.Text(f"R$ {preco}", color="#4a90e2", weight=ft.FontWeight.BOLD),
                campo
            ]),
            bgcolor="#1e2128", padding=20, border_radius=12, margin=ft.Margin(0, 0, 0, 10)
        )

    col_esquerda = ft.Column([
        ft.Text("Configuração", size=25, weight=ft.FontWeight.BOLD),
        ft.Row([drop_local, container_setores]),  # O Container que alterna os dropdowns
        ft.Divider(height=20, color="transparent"),
        ft.Text("Lançamentos", size=25, weight=ft.FontWeight.BOLD),
        criar_card("coffee", "Café da Manhã", "9,00", qtd_cafe),
        criar_card("restaurant", "Almoço Buffet", "24,00", qtd_buffet),
        criar_card("lunch_dining", "Almoço Marmita", "21,50", qtd_marmita),
        criar_card("bedtime", "Janta", "21,50", qtd_janta),
    ], expand=True, scroll=ft.ScrollMode.ADAPTIVE)

    col_direita = ft.Container(
        content=ft.Column([
            ft.Text("RESUMO FINANCEIRO", weight=ft.FontWeight.BOLD),
            ft.Divider(color="white10"),
            txt_total,
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
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=9999)