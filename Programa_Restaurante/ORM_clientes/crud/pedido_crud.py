# pedido_crud.py
from sqlalchemy.orm import Session
from models import Pedido, PedidoItem, Menu


# -------------------------
#     CREAR PEDIDO
# -------------------------
def crear_pedido(db: Session, cliente_id: int, items: list):
    """
    items = [ menu_id, menu_id, menu_id ... ]
    Cada aparición cuenta como 1 unidad.
    """
    try:
        nuevo = Pedido(cliente_id=cliente_id)
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)

        # Contar cantidades usando reduce
        from functools import reduce
        cantidades = reduce(lambda acc, menu_id: {**acc, menu_id: acc.get(menu_id, 0) + 1}, items, {})

        # Insertar items
        for menu_id, cant in cantidades.items():
            item = PedidoItem(
                pedido_id=nuevo.id,
                menu_id=menu_id,
                cantidad=cant
            )
            db.add(item)

        db.commit()
        return nuevo
    except Exception:
        db.rollback()
        return None


# -------------------------
#     OBTENER PEDIDO POR ID
# -------------------------
def obtener_pedido(db: Session, pedido_id: int):
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()


# -------------------------
#     LISTAR TODOS LOS PEDIDOS
# -------------------------
def listar_pedidos(db: Session):
    return db.query(Pedido).all()


# -------------------------
#     DETALLE DE UN PEDIDO
# -------------------------
def obtener_detalle_pedido(db: Session, pedido_id: int):
    """
    Retorna una lista como:
    [
        (nombre_menu, cantidad, precio_unitario, subtotal_linea)
    ]
    """
    pedido = obtener_pedido(db, pedido_id)
    if not pedido:
        return []

    detalle = []

    for item in pedido.items:
        menu = db.query(Menu).filter(Menu.id == item.menu_id).first()

        if menu:
            subtotal = menu.precio * item.cantidad
            detalle.append((menu.nombre, item.cantidad, menu.precio, subtotal))

    return detalle


# -------------------------
#     CALCULAR SUBTOTAL
# -------------------------
def calcular_subtotal(db: Session, pedido_id: int):
    detalle = obtener_detalle_pedido(db, pedido_id)
    return sum(linea[3] for linea in detalle)  # subtotal_linea


# -------------------------
#          IVA (19%)
# -------------------------
def calcular_iva(db: Session, pedido_id: int):
    return round(calcular_subtotal(db, pedido_id) * 0.19)


# -------------------------
#          TOTAL
# -------------------------
def calcular_total(db: Session, pedido_id: int):
    return calcular_subtotal(db, pedido_id) + calcular_iva(db, pedido_id)


# -------------------------
#     ELIMINAR PEDIDO
# -------------------------
def eliminar_pedido(db: Session, pedido_id: int):
    pedido = obtener_pedido(db, pedido_id)
    if not pedido:
        return False
    try:
        # Borrar primero los items
        for item in pedido.items:
            db.delete(item)
        db.delete(pedido)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
