import flet as ft


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "Teste de Emergencia"

    # Se o erro persistir, use o modo WEB forçado no código
    # page.launch_url = True

    def acao(e):
        print("Clicou")

    # Layout ultra simples para testar renderização
    page.add(
        ft.Text("SISTEMA DE REFEICOES", size=30, weight=ft.FontWeight.BOLD),
        ft.Dropdown(
            label="Local",
            options=[ft.dropdown.Option("Sede"), ft.dropdown.Option("Secador")]
        ),
        ft.TextField(label="Quantidade", value="0"),
        ft.ElevatedButton("TESTAR SALVAR", on_click=acao, bgcolor="blue", color="white")
    )


if __name__ == "__main__":
    # Tenta rodar normal. Se falhar, use view=ft.AppView.WEB_BROWSER
    ft.app(target=main)