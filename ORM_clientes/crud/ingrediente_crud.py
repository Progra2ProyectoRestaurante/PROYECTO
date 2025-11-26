# ingrediente_crud.py
from sqlalchemy.orm import Session
from models import Ingrediente


# -------------------------
#   OBTENER INGREDIENTE POR NOMBRE
# -------------------------
def obtener_por_nombre(db: Session, nombre: str):
    return (
        db.query(Ingrediente)
        .filter(Ingrediente.nombre == nombre)
        .first()
    )


# -------------------------
#       LISTAR INGREDIENTES
# -------------------------
def listar_ingredientes(db: Session):
    # Uso de filter para solo ingredientes con cantidad > 0
    ingredientes = db.query(Ingrediente).all()
    return list(filter(lambda i: i.cantidad > 0, ingredientes))


# -------------------------
#       CREAR INGREDIENTE
# -------------------------
def crear_ingrediente(db: Session, nombre: str, unidad: str, cantidad: float):
    if not nombre or not unidad or cantidad is None:
        return None
    existente = obtener_por_nombre(db, nombre)
    try:
        if existente:
            # Actualizar unidad y cantidad
            existente.unidad = unidad
            existente.cantidad = cantidad
            db.commit()
            db.refresh(existente)
            return existente
        nuevo = Ingrediente(
            nombre=nombre,
            unidad=unidad,
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
#   SUMAR STOCK A INGREDIENTE
# -------------------------
def sumar_stock(db: Session, nombre: str, cantidad: float):
    ing = obtener_por_nombre(db, nombre)
    if not ing:
        return None

    ing.cantidad += cantidad
    db.commit()
    db.refresh(ing)
    return ing


# -------------------------
#   RESTAR STOCK A INGREDIENTE
# -------------------------
def restar_stock(db: Session, nombre: str, cantidad: float):
    ing = obtener_por_nombre(db, nombre)
    if not ing:
        return None

    if ing.cantidad < cantidad:
        return False  # No alcanza

    ing.cantidad -= cantidad
    db.commit()
    db.refresh(ing)
    return True


# -------------------------
#    ELIMINAR INGREDIENTE
# -------------------------
def eliminar_ingrediente(db: Session, nombre: str):
    ing = obtener_por_nombre(db, nombre)
    if not ing:
        return False
    try:
        db.delete(ing)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


# -------------------------
# VALIDACIÓN DE STOCK
# -------------------------
def validar_stock(db: Session, requerimientos: dict):
    """
    requerimientos = {"tomate": 0.1, "pan": 1}
    """
    for nombre, req in requerimientos.items():
        ing = obtener_por_nombre(db, nombre)
        if not ing or ing.cantidad < req:
            return False
    return True


# -------------------------
#   LISTAR FALTANTES
# -------------------------
def faltantes(db: Session, requerimientos: dict):
    """
    Retorna lista de:
    [(nombre, requerido, disponible)]
    """
    faltas = []
    for nombre, req in requerimientos.items():
        ing = obtener_por_nombre(db, nombre)
        disp = ing.cantidad if ing else 0
        if disp < req:
            faltas.append((nombre, req, disp))
    return faltas


# -------------------------
#   DESCONTAR REQUERIMIENTOS
# -------------------------
def descontar_requerimientos(db: Session, requerimientos: dict):
    """
    Descuenta stock si alcanza, si no retorna False
    """
    if not validar_stock(db, requerimientos):
        return False

    for nombre, req in requerimientos.items():
        ing = obtener_por_nombre(db, nombre)
        ing.cantidad -= req

    db.commit()
    return True
