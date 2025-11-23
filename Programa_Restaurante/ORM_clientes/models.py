# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, engine


# -------------------------
#       CLIENTE
# -------------------------
class Cliente(Base):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=False, unique=True)

    pedidos = relationship("Pedido", back_populates="cliente")


# -------------------------
#       INGREDIENTE
# -------------------------
class Ingrediente(Base):
    __tablename__ = "ingrediente"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    unidad = Column(String, nullable=False)
    cantidad = Column(Float, nullable=False)

    menus = relationship("MenuIngrediente", back_populates="ingrediente")


# -------------------------
#       MENU
# -------------------------
class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    precio = Column(Integer, nullable=False)
    descripcion = Column(String, nullable=True)

    ingredientes = relationship("MenuIngrediente", back_populates="menu")
    items = relationship("PedidoItem", back_populates="menu")


# -------------------------
#   MENU - INGREDIENTE
# -------------------------
class MenuIngrediente(Base):
    __tablename__ = "menu_ingrediente"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menu.id"))
    ingrediente_id = Column(Integer, ForeignKey("ingrediente.id"))
    cantidad = Column(Float, nullable=False)

    menu = relationship("Menu", back_populates="ingredientes")
    ingrediente = relationship("Ingrediente", back_populates="menus")


# -------------------------
#         PEDIDO
# -------------------------
class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"))
    fecha = Column(String, nullable=False)  # Guardar fecha como string (YYYY-MM-DD)

    cliente = relationship("Cliente", back_populates="pedidos")
    items = relationship("PedidoItem", back_populates="pedido")


# -------------------------
#     PEDIDO - ITEM
# -------------------------
class PedidoItem(Base):
    __tablename__ = "pedido_item"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedido.id"))
    menu_id = Column(Integer, ForeignKey("menu.id"))
    cantidad = Column(Integer, nullable=False)

    pedido = relationship("Pedido", back_populates="items")
    menu = relationship("Menu", back_populates="items")


# -------------------------
#   CREAR TABLAS
# -------------------------
def crear_base():
    Base.metadata.create_all(bind=engine)
