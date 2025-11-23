# graficos.py
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from models import Ingrediente, Pedido, PedidoItem, Menu
from datetime import datetime


# ==========================================================
#  GRÁFICOS PRINCIPALES DEL SISTEMA
# ==========================================================

def graficar_stock(db: Session):
    """Muestra un gráfico con los 10 ingredientes con menor stock."""
    ingredientes = db.query(Ingrediente).order_by(Ingrediente.cantidad.asc()).limit(10).all()
    if not ingredientes:
        print("No hay datos disponibles para graficar stock.")
        return
    try:
        nombres = [i.nombre for i in ingredientes]
        cantidades = [i.cantidad for i in ingredientes]
        plt.figure(figsize=(10, 5))
        plt.barh(nombres, cantidades)
        plt.title("Ingredientes con Menor Stock")
        plt.xlabel("Cantidad")
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error al graficar stock: {e}")


def graficar_menus_mas_vendidos(db: Session):
    """Muestra un gráfico de barras con los menús más vendidos."""
    try:
        datos = (
            db.query(Menu.nombre, PedidoItem.cantidad)
            .join(PedidoItem, Menu.id == PedidoItem.menu_id)
            .all()
        )
        if not datos:
            print("No hay datos disponibles para graficar menús más vendidos.")
            return
        # Agrupación manual
        acumulado = {}
        for nombre, cantidad in datos:
            acumulado[nombre] = acumulado.get(nombre, 0) + cantidad
        nombres = list(acumulado.keys())
        cantidades = list(acumulado.values())
        plt.figure(figsize=(10, 5))
        plt.bar(nombres, cantidades)
        plt.title("Menús Más Vendidos")
        plt.ylabel("Cantidad")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error al graficar menús más vendidos: {e}")


def graficar_ingresos_por_dia(db: Session):
    """Gráfico de ingresos totales por día."""
    from datetime import datetime
    try:
        pedidos = db.query(Pedido).all()
        if not pedidos:
            print("No hay datos disponibles para graficar ingresos por día.")
            return
        ingresos_por_dia = {}
        for p in pedidos:
            try:
                fecha_dt = datetime.strptime(p.fecha, "%Y-%m-%d")
                fecha = fecha_dt.strftime("%d/%m/%Y")
                # Calcular total del pedido sumando los precios de los menús
                total = 0
                for item in p.items:
                    if item.menu and hasattr(item.menu, 'precio'):
                        total += item.menu.precio * item.cantidad
            except Exception:
                continue
            ingresos_por_dia[fecha] = ingresos_por_dia.get(fecha, 0) + total
        if not ingresos_por_dia:
            print("No hay datos válidos para graficar ingresos por día.")
            return
        fechas = list(ingresos_por_dia.keys())
        ingresos = list(ingresos_por_dia.values())
        plt.figure(figsize=(10, 5))
        plt.plot(fechas, ingresos, marker="o")
        plt.title("Ingresos por Día")
        plt.ylabel("Ingresos ($)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error al graficar ingresos por día: {e}")


def graficar_ingresos_totales(db: Session):
    """Gauge simple de ingresos totales acumulados."""
    try:
        pedidos = db.query(Pedido).all()
        total = 0
        for p in pedidos:
            for item in p.items:
                if item.menu and hasattr(item.menu, 'precio'):
                    total += item.menu.precio * item.cantidad
        plt.figure(figsize=(6, 4))
        plt.bar(["Ingresos Totales"], [total], color="green")
        plt.title("Ingresos Totales")
        plt.ylabel("Total ($)")
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error al graficar ingresos totales: {e}")


def graficar_ingresos_por_mes(db: Session):
    """Gráfico de ingresos totales por mes."""
    from datetime import datetime
    try:
        pedidos = db.query(Pedido).all()
        if not pedidos:
            print("No hay datos disponibles para graficar ingresos por mes.")
            return
        ingresos_por_mes = {}
        for p in pedidos:
            try:
                fecha_dt = datetime.strptime(p.fecha, "%Y-%m-%d")
                fecha = fecha_dt.strftime("%Y-%m")
                total = 0
                for item in p.items:
                    if item.menu and hasattr(item.menu, 'precio'):
                        total += item.menu.precio * item.cantidad
            except Exception:
                continue
            ingresos_por_mes[fecha] = ingresos_por_mes.get(fecha, 0) + total
        if not ingresos_por_mes:
            print("No hay datos válidos para graficar ingresos por mes.")
            return
        meses = list(ingresos_por_mes.keys())
        ingresos = list(ingresos_por_mes.values())
        plt.figure(figsize=(10, 5))
        plt.plot(meses, ingresos, marker="o")
        plt.title("Ingresos por Mes")
        plt.ylabel("Ingresos ($)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error al graficar ingresos por mes: {e}")


def graficar_uso_ingredientes(db: Session):
    """Gráfico de uso de ingredientes en todos los pedidos realizados."""
    try:
        items = db.query(PedidoItem).all()
        if not items:
            print("No hay datos disponibles para graficar uso de ingredientes.")
            return
        # Acumular ingredientes usados por nombre
        uso = {}
        for item in items:
            menu = db.query(Menu).get(item.menu_id)
            if not menu:
                continue
            from logic.Menu import Menu as MenuLogic
            reqs = MenuLogic.requerimientos(menu.nombre, db=db)
            for ing, cant in reqs.items():
                uso[ing] = uso.get(ing, 0) + cant * item.cantidad
        if not uso:
            print("No hay datos válidos para graficar uso de ingredientes.")
            return
        nombres = list(uso.keys())
        cantidades = list(uso.values())
        plt.figure(figsize=(10, 5))
        plt.bar(nombres, cantidades)
        plt.title("Uso de Ingredientes en Pedidos")
        plt.ylabel("Cantidad usada")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error al graficar uso de ingredientes: {e}")


# ==========================================================
#  FUNCIÓN CENTRAL PARA MOSTRAR TODOS LOS GRÁFICOS
# ==========================================================

def mostrar_graficos(db: Session):
    """
    Muestra todos los gráficos del sistema en ventanas separadas.
    IMPORTANTE:
    - Llamar como mostrar_graficos(db)
    """
    graficar_stock(db)
    graficar_menus_mas_vendidos(db)
    graficar_ingresos_por_dia(db)
    graficar_ingresos_totales(db)
    graficar_ingresos_por_mes(db)
    graficar_uso_ingredientes(db)
