import flet as ft

def main(page: ft.Page):
    # --- Configuration de base de la page ---
    page.title = "إدارة المتجر"
    page.rtl = True  # Indispensable pour l'affichage de droite à gauche en arabe
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # --- Barre d'en-tête (AppBar) ---
    page.appbar = ft.AppBar(
        title=ft.Text("إدارة المتجر", weight=ft.FontWeight.BOLD),
        center_title=False,
        actions=[
            ft.IconButton(ft.icons.BRIGHTNESS_4),
            ft.IconButton(ft.icons.CLOUD_UPLOAD),
            ft.IconButton(ft.icons.HISTORY),
        ],
    )

    # --- Menu de navigation (Boutons du haut) ---
    nav_buttons = ft.Row(
        [
            ft.ElevatedButton("المخزون", style=ft.ButtonStyle(color=ft.colors.BLUE)), # Onglet actif
            ft.OutlinedButton("نقطة البيع"),
            ft.OutlinedButton("السجل"),
            ft.OutlinedButton("الإعدادات"),
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    # --- Sous-menu (Gestion Catégories/Fournisseurs) ---
    sub_menu = ft.Row(
        [
            ft.TextButton("إدارة الموردين 👥", icon=ft.icons.PEOPLE),
            ft.TextButton("إدارة الفئات 📁", icon=ft.icons.FOLDER),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # --- Formulaire d'ajout de produit ---
    form_title = ft.Text("إضافة منتج جديد للمخزن:", size=18, weight=ft.FontWeight.BOLD)
    
    nom_produit = ft.TextField(label="اسم المنتج")
    
    row_categorie_fournisseur = ft.Row([
        ft.Dropdown(label="الفئة", expand=True, options=[ft.dropdown.Option("فئة 1")]),
        ft.Dropdown(label="المورد", expand=True, options=[ft.dropdown.Option("مورد 1")]),
    ])

    row_prix = ft.Row([
        ft.TextField(label="سعر الشراء (دج)", value="0.0", expand=True, keyboard_type=ft.KeyboardType.NUMBER),
        ft.TextField(label="سعر البيع (دج)", value="0.0", expand=True, keyboard_type=ft.KeyboardType.NUMBER),
    ])

    row_quantite_taxe = ft.Row([
        ft.TextField(label="الضريبة (%)", value="0.0", expand=True, keyboard_type=ft.KeyboardType.NUMBER),
        ft.TextField(label="الكمية المتوفرة", value="0", expand=True, keyboard_type=ft.KeyboardType.NUMBER),
    ])

    row_alerte_code = ft.Row([
        ft.TextField(label="حد التنبيه", value="3", expand=True, keyboard_type=ft.KeyboardType.NUMBER),
        ft.TextField(label="رقم الباركود", expand=True),
    ])

    # Fonction simulée pour le bouton de sauvegarde
    def sauvegarder_produit(e):
        # Pour l'instant, on affiche juste un message de succès en bas de l'écran
        snack_bar = ft.SnackBar(ft.Text(f"تم حفظ المنتج: {nom_produit.value}"))
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()

    btn_sauvegarder = ft.ElevatedButton(
        "حفظ المنتج", 
        bgcolor=ft.colors.GREEN, 
        color=ft.colors.WHITE,
        width=200,
        on_click=sauvegarder_produit
    )

    # --- Barre de recherche en bas ---
    search_row = ft.Row([
        ft.TextField(label="بحث عن منتج...", prefix_icon=ft.icons.SEARCH, expand=True),
        ft.Dropdown(label="تصفية حسب الفئة", width=150),
    ])

    # --- Assemblage de la page ---
    page.add(
        nav_buttons,
        ft.Divider(),
        sub_menu,
        ft.Divider(),
        form_title,
        nom_produit,
        row_categorie_fournisseur,
        row_prix,
        row_quantite_taxe,
        row_alerte_code,
        ft.Row([btn_sauvegarder], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        search_row
    )

ft.app(target=main)