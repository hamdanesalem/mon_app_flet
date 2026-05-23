import flet as ft
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
import csv, os, shutil
from pathlib import Path
import hashlib

# ------------------------------------------------------------
# قاعدة البيانات
# ------------------------------------------------------------
Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class Supplier(Base):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact = Column(String)
    phone = Column(String)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    price = Column(Float, default=0.0)
    purchase_price = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)
    alert_threshold = Column(Integer, default=3)
    barcode = Column(String, unique=True, nullable=True)
    category = relationship("Category")
    supplier = relationship("Supplier")

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now)
    total_amount = Column(Float, default=0.0)

class SaleItem(Base):
    __tablename__ = 'sale_items'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    price_at_time = Column(Float)

engine = create_engine('sqlite:///magasin.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def init_default():
    for cat in ["مواد غذائية", "إلكترونيات", "ملابس", "أخرى"]:
        if not session.query(Category).filter_by(name=cat).first():
            session.add(Category(name=cat))
    if not session.query(Supplier).first():
        session.add(Supplier(name="مورد افتراضي", contact="", phone=""))
    session.commit()
init_default()

# ------------------------------------------------------------
# التطبيق الرئيسي
# ------------------------------------------------------------
def main(page: ft.Page):
    page.rtl = True
    page.title = "إدارة المتجر"
    page.padding = 10
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400
    page.window.height = 700

    editing_product_id = None
    cart = {}
    current_section = "stock"

    def show_snackbar(msg, is_error=False):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor="red" if is_error else "green", duration=2000)
        page.snack_bar.open = True
        page.update()

    def backup(e):
        shutil.copy("magasin.db", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        show_snackbar("تم النسخ الاحتياطي")

    def restore(e):
        backups = list(Path(".").glob("backup_*.db"))
        if backups:
            shutil.copy(max(backups, key=os.path.getctime), "magasin.db")
            show_snackbar("تمت الاستعادة، أعد تشغيل التطبيق")
        else:
            show_snackbar("لا يوجد نسخة احتياطية", True)

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.update()

    # ----- الفئات -----
    categories_list = ft.ListView(expand=True, spacing=10)
    new_cat_field = ft.TextField(label="اسم الفئة", width=300)

    def load_categories():
        categories_list.controls.clear()
        for c in session.query(Category).all():
            categories_list.controls.append(
                ft.Container(
                    content=ft.Row([ft.Text(c.name, expand=True), ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, cid=c.id: delete_category(cid))]),
                    padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5
                ))
        page.update()

    def add_category(e):
        name = new_cat_field.value.strip()
        if name and not session.query(Category).filter_by(name=name).first():
            session.add(Category(name=name))
            session.commit()
            show_snackbar(f"تمت إضافة '{name}'")
            new_cat_field.value = ""
            load_categories()
            refresh_dropdowns()
        elif name:
            show_snackbar("الفئة موجودة", True)

    def delete_category(cid):
        cat = session.query(Category).get(cid)
        if cat and not session.query(Product).filter_by(category_id=cid).first():
            session.delete(cat)
            session.commit()
            show_snackbar(f"تم حذف '{cat.name}'")
            load_categories()
            refresh_dropdowns()
        else:
            show_snackbar("لا يمكن الحذف: هناك منتجات تستخدمها", True)

    # ----- الموردين -----
    supplier_list = ft.ListView(expand=True, spacing=10)
    sup_name = ft.TextField(label="اسم المورد", expand=True)
    sup_contact = ft.TextField(label="جهة اتصال")
    sup_phone = ft.TextField(label="الهاتف")

    def load_suppliers():
        supplier_list.controls.clear()
        for s in session.query(Supplier).all():
            supplier_list.controls.append(
                ft.Container(
                    content=ft.Row([ft.Text(f"{s.name} - {s.contact} - {s.phone}", expand=True), ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=lambda e, sid=s.id: delete_supplier(sid))]),
                    padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5
                ))
        page.update()

    def add_supplier(e):
        if sup_name.value:
            s = Supplier(name=sup_name.value, contact=sup_contact.value, phone=sup_phone.value)
            session.add(s)
            session.commit()
            show_snackbar("تمت إضافة المورد")
            sup_name.value = sup_contact.value = sup_phone.value = ""
            load_suppliers()
            refresh_dropdowns()

    def delete_supplier(sid):
        sup = session.query(Supplier).get(sid)
        if sup and not session.query(Product).filter_by(supplier_id=sid).first():
            session.delete(sup)
            session.commit()
            show_snackbar("تم حذف المورد")
            load_suppliers()
            refresh_dropdowns()
        else:
            show_snackbar("لا يمكن الحذف: هناك منتجات مرتبطة", True)

    # ----- المنتجات (المخزون) -----
    prod_name = ft.TextField(label="الاسم", expand=True)
    cat_drop = ft.Dropdown(label="الفئة", options=[], expand=True)
    sup_drop = ft.Dropdown(label="المورد", options=[], expand=True)
    price_sale = ft.TextField(label="سعر البيع", value="0.0", expand=True)
    price_purchase = ft.TextField(label="سعر الشراء", value="0.0", expand=True)
    tax = ft.TextField(label="الضريبة (%)", value="0.0", expand=True)
    qty = ft.TextField(label="الكمية", value="0", expand=True)
    threshold = ft.TextField(label="حد التنبيه", value="3", expand=True)
    barcode = ft.TextField(label="الباركود", value="", expand=True)

    btn_save = ft.FilledButton("حفظ", on_click=lambda e: save_product(), style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE))
    btn_cancel_edit = ft.TextButton("إلغاء", on_click=lambda e: cancel_edit(), visible=False, style=ft.ButtonStyle(color=ft.Colors.RED))

    search = ft.TextField(label="بحث...", prefix_icon=ft.Icons.SEARCH, expand=True, on_change=lambda e: load_products())
    filter_cat = ft.Dropdown(label="تصفية حسب الفئة", options=[], expand=True, on_select=lambda e: load_products())
    list_title = ft.Text("الكتالوج:", weight="bold", size=16)
    product_list = ft.ListView(expand=True, spacing=10)
    total_value = ft.Text("", weight="bold", size=15, color=ft.Colors.GREEN)
    total_items = ft.Text("", weight="bold", size=15, color=ft.Colors.BLUE)
    export_btn = ft.FilledButton("تصدير CSV", on_click=lambda e: export_stock(), style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE))

    def refresh_dropdowns():
        cats = session.query(Category).all()
        sups = session.query(Supplier).all()
        cat_opts = [ft.dropdown.Option("", "الكل")] + [ft.dropdown.Option(str(c.id), c.name) for c in cats]
        filter_cat.options = cat_opts
        cat_drop.options = cat_opts[1:]
        sup_drop.options = [ft.dropdown.Option(str(s.id), s.name) for s in sups]
        page.update()

    def load_products():
        product_list.controls.clear()
        q = session.query(Product)
        txt = search.value.lower() if search.value else ""
        if txt:
            q = q.filter(Product.name.contains(txt))
        f = filter_cat.value
        if f and f.isdigit():
            q = q.filter(Product.category_id == int(f))
        prods = q.all()
        total_val = sum(p.price * p.quantity for p in prods)
        total_qty = sum(p.quantity for p in prods)
        for p in prods:
            is_low = p.quantity <= p.alert_threshold
            color = ft.Colors.ORANGE if is_low else ft.Colors.BLACK
            cat_name = p.category.name if p.category else "-"
            product_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{p.name} ({cat_name}) | {p.price:,.2f} دج | الكمية:{p.quantity} | حد:{p.alert_threshold}" + (" ⚠️" if is_low else ""),
                                expand=True, color=color, weight="bold" if is_low else "normal"),
                        ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE, on_click=lambda e, pid=p.id: start_edit(pid)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, pid=p.id, name=p.name: confirm_delete(pid, name)),
                        ft.IconButton(icon=ft.Icons.ADD_BOX, icon_color=ft.Colors.GREEN, on_click=lambda e, pid=p.id: replenish(pid))
                    ]), padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5
                ))
        total_value.value = f"قيمة المخزون: {total_val:,.2f} دج"
        total_items.value = f"عدد القطع: {total_qty}"
        page.update()

    def replenish(pid):
        p = session.query(Product).get(pid)
        if p:
            p.quantity += 10
            session.commit()
            show_snackbar(f"تمت إضافة 10 إلى {p.name}")
            load_products()
            load_pos()

    def start_edit(pid):
        nonlocal editing_product_id
        p = session.query(Product).get(pid)
        if p:
            editing_product_id = p.id
            prod_name.value = p.name
            price_sale.value = str(p.price)
            price_purchase.value = str(p.purchase_price)
            tax.value = str(p.tax_rate)
            qty.value = str(p.quantity)
            threshold.value = str(p.alert_threshold)
            barcode.value = p.barcode or ""
            cat_drop.value = str(p.category_id) if p.category_id else ""
            sup_drop.value = str(p.supplier_id) if p.supplier_id else ""
            btn_save.text = "تعديل"
            btn_cancel_edit.visible = True
            page.update()

    def cancel_edit():
        nonlocal editing_product_id
        editing_product_id = None
        prod_name.value = price_sale.value = price_purchase.value = tax.value = ""
        qty.value = "0"
        threshold.value = "3"
        barcode.value = ""
        cat_drop.value = sup_drop.value = ""
        btn_save.text = "حفظ"
        btn_cancel_edit.visible = False
        page.update()

    def save_product():
        nonlocal editing_product_id
        name = prod_name.value.strip()
        if not name:
            show_snackbar("الاسم مطلوب", True)
            return
        try: sale_price = float(price_sale.value)
        except: sale_price = 0.0
        try: pur_price = float(price_purchase.value)
        except: pur_price = 0.0
        try: tax_rate = float(tax.value)
        except: tax_rate = 0.0
        try: quant = int(qty.value)
        except: quant = 0
        try: thr = int(threshold.value)
        except: thr = 3
        cat_id = int(cat_drop.value) if cat_drop.value and cat_drop.value.isdigit() else None
        sup_id = int(sup_drop.value) if sup_drop.value and sup_drop.value.isdigit() else None
        bc = barcode.value.strip() or None

        if editing_product_id:
            p = session.query(Product).get(editing_product_id)
            if p:
                p.name = name
                p.price = sale_price
                p.purchase_price = pur_price
                p.tax_rate = tax_rate
                p.quantity = quant
                p.alert_threshold = thr
                p.category_id = cat_id
                p.supplier_id = sup_id
                p.barcode = bc
                session.commit()
                show_snackbar(f"تم تعديل {name}")
            editing_product_id = None
            btn_save.text = "حفظ"
            btn_cancel_edit.visible = False
        else:
            new_p = Product(name=name, price=sale_price, purchase_price=pur_price, tax_rate=tax_rate,
                            quantity=quant, alert_threshold=thr, category_id=cat_id, supplier_id=sup_id, barcode=bc)
            session.add(new_p)
            session.commit()
            show_snackbar(f"تمت إضافة {name}")
        prod_name.value = price_sale.value = price_purchase.value = tax.value = ""
        qty.value = "0"
        threshold.value = "3"
        barcode.value = ""
        cat_drop.value = sup_drop.value = ""
        search.value = ""
        filter_cat.value = ""
        load_products()
        load_pos()
        page.update()

    def confirm_delete(pid, name):
        def delete_action(e):
            p = session.query(Product).get(pid)
            if p:
                session.delete(p)
                session.commit()
                show_snackbar(f"تم حذف {name}")
                load_products()
                load_pos()
            dlg.open = False
            page.update()
        dlg = ft.AlertDialog(title=ft.Text("تأكيد الحذف"), content=ft.Text(f"حذف {name} ؟"), actions=[ft.TextButton("إلغاء", on_click=lambda e: setattr(dlg, 'open', False)), ft.TextButton("حذف", on_click=delete_action)])
        page.dialog = dlg
        dlg.open = True
        page.update()

    def export_stock():
        with open("stock_export.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID","الاسم","الفئة","سعر البيع","سعر الشراء","الضريبة","الكمية","الحد","الباركود"])
            for p in session.query(Product).all():
                w.writerow([p.id, p.name, p.category.name if p.category else "", p.price, p.purchase_price, p.tax_rate, p.quantity, p.alert_threshold, p.barcode])
        show_snackbar("تم تصدير المخزون")

    # ----- نقطة البيع -----
    pos_list = ft.ListView(expand=True, spacing=10)
    cart_list = ft.ListView(expand=True, spacing=10)
    cart_title = ft.Text("السلة", size=18, weight="bold")
    total_pay = ft.Text("0.00 دج", size=24, weight="bold", color=ft.Colors.RED)
    total_label = ft.Text("الإجمالي:")
    checkout_btn = ft.FilledButton("إتمام البيع", on_click=lambda e: checkout(), style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE))
    clear_cart_btn = ft.TextButton("تفريغ", on_click=lambda e: clear_cart(), style=ft.ButtonStyle(color=ft.Colors.RED))
    pos_filter = ft.Dropdown(label="تصفية حسب الفئة", options=[], expand=True, on_select=lambda e: load_pos())
    barcode_input = ft.TextField(label="الباركود", hint_text="امسح أو اكتب", on_submit=lambda e: add_by_barcode(e.control.value), expand=True)

    def load_pos():
        pos_list.controls.clear()
        q = session.query(Product).filter(Product.quantity > 0)
        f = pos_filter.value
        if f and f.isdigit():
            q = q.filter(Product.category_id == int(f))
        for p in q.all():
            pos_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Text(p.name, weight="bold"), ft.Text(f"{p.price:,.2f} دج", size=12), ft.Text(f"المخزون: {p.quantity}", size=10, color=ft.Colors.GREY)], expand=True),
                        ft.IconButton(icon=ft.Icons.ADD_SHOPPING_CART, icon_color=ft.Colors.GREEN, on_click=lambda e, prod=p: add_to_cart(prod))
                    ]), padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5
                ))
        page.update()

    def add_by_barcode(code):
        if code:
            p = session.query(Product).filter_by(barcode=code).first()
            if p:
                add_to_cart(p)
                barcode_input.value = ""
                page.update()
            else:
                show_snackbar("الباركود غير موجود", True)

    def add_to_cart(prod):
        if prod.id in cart:
            if cart[prod.id]['qty'] < prod.quantity:
                cart[prod.id]['qty'] += 1
            else:
                show_snackbar(f"{prod.name} : المخزون غير كاف", True)
                return
        else:
            cart[prod.id] = {'name': prod.name, 'price': prod.price, 'qty': 1}
        update_cart()

    def remove_from_cart(pid):
        if pid in cart:
            cart[pid]['qty'] -= 1
            if cart[pid]['qty'] <= 0:
                del cart[pid]
            update_cart()

    def inc_cart(pid):
        if pid in cart:
            prod = session.query(Product).get(pid)
            if prod and cart[pid]['qty'] < prod.quantity:
                cart[pid]['qty'] += 1
                update_cart()
            else:
                show_snackbar(f"{cart[pid]['name']} : المخزون غير كاف", True)

    def clear_cart():
        cart.clear()
        update_cart()

    def update_cart():
        cart_list.controls.clear()
        total = 0.0
        for pid, item in cart.items():
            line = item['price'] * item['qty']
            total += line
            cart_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{item['qty']}x {item['name']}", expand=True),
                        ft.Text(f"{line:,.2f} دج", weight="bold"),
                        ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ft.Colors.GREEN, on_click=lambda e, id=pid: inc_cart(id)),
                        ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=ft.Colors.RED, on_click=lambda e, id=pid: remove_from_cart(id))
                    ]), padding=5, bgcolor=ft.Colors.WHITE, border_radius=5
                ))
        total_pay.value = f"{total:,.2f} دج"
        page.update()

    def checkout():
        if not cart:
            show_snackbar("السلة فارغة", True)
            return
        for pid, item in cart.items():
            prod = session.query(Product).get(pid)
            if not prod or prod.quantity < item['qty']:
                show_snackbar(f"المخزون غير كاف لـ {item['name']}", True)
                return
        total = sum(item['price'] * item['qty'] for item in cart.values())
        sale = Sale(total_amount=total, date=datetime.now())
        session.add(sale)
        session.flush()
        for pid, item in cart.items():
            prod = session.query(Product).get(pid)
            prod.quantity -= item['qty']
            session.add(SaleItem(sale_id=sale.id, product_id=pid, quantity=item['qty'], price_at_time=item['price']))
        session.commit()
        cart.clear()
        update_cart()
        show_snackbar("تمت عملية البيع")
        load_products()
        load_pos()
        load_history()
        load_stats()

    # ----- السجل -----
    history_list = ft.ListView(expand=True, spacing=10)
    export_history_btn = ft.FilledButton("تصدير CSV", on_click=lambda e: export_history(), style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE))

    def load_history():
        history_list.controls.clear()
        for sale in session.query(Sale).order_by(Sale.date.desc()).all():
            items = session.query(SaleItem).filter_by(sale_id=sale.id).all()
            details = "\n".join([f"{i.quantity}x {i.product.name} ({i.price_at_time:.2f} دج)" for i in items])
            history_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([ft.Text(f"رقم:{sale.id} - {sale.date.strftime('%d/%m/%Y %H:%M')}", weight="bold"), ft.Text(f"{sale.total_amount:,.2f} دج", color=ft.Colors.GREEN)]),
                        ft.Text(details, size=12, color=ft.Colors.GREY),
                        ft.Row([ft.TextButton("إلغاء البيع", on_click=lambda e, sid=sale.id: cancel_sale(sid), style=ft.ButtonStyle(color=ft.Colors.RED))])
                    ]), padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5
                ))
        page.update()

    def cancel_sale(sid):
        sale = session.query(Sale).get(sid)
        if sale:
            for item in session.query(SaleItem).filter_by(sale_id=sid).all():
                prod = session.query(Product).get(item.product_id)
                if prod:
                    prod.quantity += item.quantity
            session.delete(sale)
            session.commit()
            show_snackbar(f"تم إلغاء البيع #{sid}")
            load_history()
            load_products()
            load_pos()
            load_stats()

    def export_history():
        with open("history_export.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID","التاريخ","الإجمالي"])
            for s in session.query(Sale).order_by(Sale.date.desc()).all():
                w.writerow([s.id, s.date.strftime("%Y-%m-%d %H:%M"), s.total_amount])
        show_snackbar("تم تصدير السجل")

    # ----- لوحة المعلومات (بدون رسم بياني) -----
    stats_text = ft.Text("", size=16)
    low_stock_list = ft.ListView(height=200)

    def load_stats():
        total_rev = session.query(func.sum(Sale.total_amount)).scalar() or 0.0
        nb_sales = session.query(Sale).count()
        best = session.query(SaleItem.product_id, func.sum(SaleItem.quantity).label('q')).group_by(SaleItem.product_id).order_by(func.sum(SaleItem.quantity).desc()).first()
        best_name = ""
        if best:
            p = session.query(Product).get(best[0])
            best_name = f"{p.name} ({best[1]} مباع)" if p else "?"
        low = session.query(Product).filter(Product.quantity <= Product.alert_threshold).all()
        low_stock_list.controls.clear()
        for p in low:
            low_stock_list.controls.append(ft.Text(f"{p.name} : {p.quantity} (الحد {p.alert_threshold})", color=ft.Colors.ORANGE))
        stats_text.value = f"""إجمالي المبيعات: {total_rev:,.2f} دج
عدد الفواتير: {nb_sales}
الأكثر مبيعاً: {best_name}
المنتجات تحت الحد: {len(low)}"""
        page.update()

    # ----- قائمة جانبية (Drawer) -----
    def on_drawer_change(e):
        idx = e.control.selected_index
        sections = ["stock", "pos", "history", "stats", "suppliers", "categories"]
        change_section(sections[idx])

    def change_section(section):
        nonlocal current_section
        current_section = section
        stock_view.visible = (section == "stock")
        pos_view.visible = (section == "pos")
        history_view.visible = (section == "history")
        stats_view.visible = (section == "stats")
        suppliers_view.visible = (section == "suppliers")
        categories_view.visible = (section == "categories")
        page.drawer.open = False
        page.update()

    drawer = ft.NavigationDrawer(
        controls=[
            ft.NavigationDrawerDestination(icon=ft.Icons.STORE, label="المخزون"),
            ft.NavigationDrawerDestination(icon=ft.Icons.SHOPPING_CART, label="نقطة البيع"),
            ft.NavigationDrawerDestination(icon=ft.Icons.HISTORY, label="السجل"),
            ft.NavigationDrawerDestination(icon=ft.Icons.DASHBOARD, label="لوحة المعلومات"),
            ft.NavigationDrawerDestination(icon=ft.Icons.PEOPLE, label="الموردين"),
            ft.NavigationDrawerDestination(icon=ft.Icons.CATEGORY, label="الفئات"),
        ],
        on_change=on_drawer_change
    )
    page.drawer = drawer

    # ----- شريط علوي -----
    def open_drawer(e):
        page.drawer.open = True
        page.update()

    top_bar = ft.Row([
        ft.IconButton(icon=ft.Icons.MENU, on_click=open_drawer),
        ft.Text("إدارة المتجر", size=18, weight="bold", expand=True, text_align=ft.TextAlign.CENTER),
        ft.IconButton(icon=ft.Icons.BRIGHTNESS_6, on_click=toggle_theme),
        ft.IconButton(icon=ft.Icons.BACKUP, on_click=backup),
        ft.IconButton(icon=ft.Icons.RESTORE, on_click=restore),
    ])

    # ----- بناء الواجهات -----
    stock_view = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Text("منتج", size=18, weight="bold"),
            prod_name,
            cat_drop,
            sup_drop,
            price_sale,
            price_purchase,
            tax,
            qty,
            threshold,
            barcode,
            ft.Row([btn_save, btn_cancel_edit], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ft.Divider(),
            ft.Row([search, filter_cat], spacing=5),
            export_btn,
            list_title,
            product_list,
            ft.Divider(),
            ft.Row([total_items, total_value], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=8, scroll=ft.ScrollMode.AUTO),
        visible=True
    )

    pos_view = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Text("نقطة البيع", size=18, weight="bold"),
            pos_filter,
            barcode_input,
            ft.Text("المنتجات المتاحة:", weight="bold"),
            ft.Container(pos_list, height=300),
            ft.Divider(),
            cart_title,
            ft.Container(cart_list, height=200),
            total_label,
            total_pay,
            ft.Row([checkout_btn, clear_cart_btn], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        ], spacing=8, scroll=ft.ScrollMode.AUTO),
        visible=False
    )

    history_view = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Row([ft.Text("السجل", size=18, weight="bold"), export_history_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            history_list
        ], spacing=8, scroll=ft.ScrollMode.AUTO),
        visible=False
    )

    stats_view = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Text("لوحة المعلومات", size=18, weight="bold"),
            stats_text,
            ft.Divider(),
            ft.Text("المنتجات تحت الحد:", weight="bold"),
            low_stock_list
        ], spacing=8, scroll=ft.ScrollMode.AUTO),
        visible=False
    )

    suppliers_view = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Text("الموردين", size=18, weight="bold"),
            sup_name,
            sup_contact,
            sup_phone,
            ft.FilledButton("إضافة مورد", on_click=add_supplier, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)),
            ft.Divider(),
            supplier_list
        ], spacing=8, scroll=ft.ScrollMode.AUTO),
        visible=False
    )

    categories_view = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Text("الفئات", size=18, weight="bold"),
            ft.Row([new_cat_field, ft.IconButton(icon=ft.Icons.ADD, on_click=add_category, icon_color=ft.Colors.GREEN)]),
            ft.Divider(),
            categories_list
        ], spacing=8, scroll=ft.ScrollMode.AUTO),
        visible=False
    )

    page.add(
        top_bar,
        stock_view,
        pos_view,
        history_view,
        stats_view,
        suppliers_view,
        categories_view
    )

    # تهيئة أولية
    refresh_dropdowns()
    load_products()
    load_pos()
    load_stats()
    load_suppliers()
    load_categories()
    page.update()

ft.run(main)
