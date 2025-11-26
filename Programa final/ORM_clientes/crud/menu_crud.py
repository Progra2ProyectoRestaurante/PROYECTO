# menu_crud.py
from sqlalchemy.orm import Session
from models import Menu, MenuIngrediente, Ingrediente


# -------------------------
#   CREAR MENÚ
# -------------------------
def crear_menu(db: Session, nombre: str, precio: int, descripcion: str = None):
    """
    Crea un menú si no existe. Si existe lo retorna.
    """
    if not nombre or precio is None or precio <= 0:
        return None
    existente = (
        db.query(Menu)
        .filter(Menu.nombre == nombre)
        .first()
    )
    if existente:
        return existente
    try:
        nuevo = Menu(nombre=nombre, precio=precio, descripcion=descripcion)
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except Exception:
        db.rollback()
        return None


# -------------------------
#   LISTAR TODOS LOS MENÚS
# -------------------------
def listar_menus(db: Session):
    # Uso de map para devolver lista de menús
    menus = db.query(Menu).all()
    return list(map(lambda m: m, menus))


# -------------------------
#   OBTENER MENÚ POR NOMBRE
# -------------------------
def obtener_menu_por_nombre(db: Session, nombre: str):
    return (
        db.query(Menu)
        .filter(Menu.nombre == nombre)
        .first()
    )


# -------------------------
#   ASIGNAR INGREDIENTE A MENÚ
# -------------------------
def agregar_ingrediente_a_menu(db: Session, menu_id: int, ingrediente_id: int, cantidad: float):
    """
    Asocia un ingrediente con un menú.
    Si ya existe la relación, actualiza la cantidad.
    """
    if cantidad is None or cantidad <= 0:
        return None
    existente = (
        db.query(MenuIngrediente)
        .filter(
            MenuIngrediente.menu_id == menu_id,
            MenuIngrediente.ingrediente_id == ingrediente_id
        )
        .first()
    )
    try:
        if existente:
            existente.cantidad = cantidad
            db.commit()
            db.refresh(existente)
            return existente
        nuevo = MenuIngrediente(
            menu_id=menu_id,
            ingrediente_id=ingrediente_id,
            cantidad=cantidad
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except Exception:
        db.rollback()
        return None


# -------------------------
#   REQUERIMIENTOS DE UN MENÚ
# -------------------------
def requerimientos_menu(db: Session, menu_id: int):
    """
    Retorna un diccionario:
    {
        "tomate": 0.1,
        "pan": 1,
        ...
    }
    """
    reqs = (
        db.query(MenuIngrediente)
        .filter(MenuIngrediente.menu_id == menu_id)
        .all()
    )

    resultado = {}
    for r in reqs:
        ingrediente = db.query(Ingrediente).filter(Ingrediente.id == r.ingrediente_id).first()
        if ingrediente:
            resultado[ingrediente.nombre] = r.cantidad

    return resultado


# -------------------------
#   OBTENER PRECIO DEL MENÚ
# -------------------------
def precio_menu(db: Session, menu_id: int):
    m = db.query(Menu).filter(Menu.id == menu_id).first()
    return m.precio if m else 0


# -------------------------
#   OBTENER INGREDIENTES DE MENÚ (DETALLADO)
# -------------------------
def ingredientes_de_menu(db: Session, menu_id: int):
    """
    Retorna:
    [
        (nombre_ingrediente, cantidad, unidad)
    ]
    """
    enlaces = (
        db.query(MenuIngrediente)
        .filter(MenuIngrediente.menu_id == menu_id)
        .all()
    )

    resultado = []

    for enlace in enlaces:
        ing = (
            db.query(Ingrediente)
            .filter(Ingrediente.id == enlace.ingrediente_id)
            .first()
        )
        if ing:
            resultado.append((ing.nombre, enlace.cantidad, ing.unidad))

    return resultado