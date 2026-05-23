import flet as ft

def main(page: ft.Page):
    page.title = "Test"
    page.add(
        ft.Text("L'application fonctionne !", size=30, color="green")
    )

ft.run(main)
