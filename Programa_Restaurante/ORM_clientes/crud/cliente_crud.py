# cliente_crud.py
from sqlalchemy.orm import Session
from models import Cliente


# -------------------------
#     CREAR CLIENTE
# -------------------------
def crear_cliente(db: Session, nombre: str, correo: str):
    """
    Crea un cliente si no existe y lo retorna.
    Si ya existe por correo, retorna el existente.
    """
    if not nombre or not correo:
        return None  # Validación de campos vacíos
    existente = (
        db.query(Cliente)
        .filter(Cliente.correo == correo)
        .first()
    )
    if existente:
        return existente
    try:
        nuevo = Cliente(nombre=nombre, correo=correo)
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except Exception:
        db.rollback()
        return None


# -------------------------
#   OBTENER CLIENTE POR ID
# -------------------------
def obtener_cliente(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


# -------------------------
#   OBTENER CLIENTE POR CORREO
# -------------------------
def obtener_cliente_por_correo(db: Session, correo: str):
    return db.query(Cliente).filter(Cliente.correo == correo).first()


# -------------------------
#     LISTAR CLIENTES
# -------------------------
def listar_clientes(db: Session):
    # Uso de map para devolver lista de clientes
    clientes = db.query(Cliente).all()
    return list(map(lambda c: c, clientes))


# -------------------------
#     BORRAR CLIENTE
# -------------------------
def eliminar_cliente(db: Session, cliente_id: int):
    cliente = obtener_cliente(db, cliente_id)
    if not cliente:
        return False
    # Impedir eliminar si tiene pedidos asociados
    if hasattr(cliente, 'pedidos') and cliente.pedidos:
        return False
    try:
        db.delete(cliente)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


# -------------------------
#  ACTUALIZAR CLIENTE
# -------------------------
def actualizar_cliente(db: Session, cliente_id: int, nombre=None, correo=None):
    cliente = obtener_cliente(db, cliente_id)
    if not cliente:
        return None
    if nombre:
        cliente.nombre = nombre
    if correo:
        # Validar unicidad de correo
        existente = db.query(Cliente).filter(Cliente.correo == correo, Cliente.id != cliente_id).first()
        if existente:
            return None
        cliente.correo = correo
    try:
        db.commit()
        db.refresh(cliente)
        return cliente
    except Exception:
        db.rollback()
        return None
