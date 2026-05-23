import flet as ft
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)

engine = create_engine('sqlite:///magasin.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Ajouter un produit par défaut si la table est vide
if not session.query(Product).first():
    session.add(Product(name="Produit test", price=10.0, quantity=5))
    session.commit()

def main(page: ft.Page):
    page.title = "Liste des produits"
    
    # Charger les produits
    products = session.query(Product).all()
    
    # Créer une ListView
    list_view = ft.ListView(expand=True, spacing=10)
    for p in products:
        list_view.controls.append(
            ft.Container(
                content=ft.Text(f"{p.name} - {p.price} DA - Stock: {p.quantity}"),
                padding=10,
                bgcolor=ft.Colors.GREY_100,
                border_radius=5
            )
        )
    
    page.add(list_view)

ft.run(main)
