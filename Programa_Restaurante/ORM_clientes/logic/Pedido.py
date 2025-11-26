# logic/Pedido.py
from logic.Stock import Stock

IVA = 0.19

class Pedido:
    def __init__(self, stock: Stock, db=None):
        self.stock = stock
        self.items = {}  # menu -> cantidad
        self.db = db

    def agregar_item(self, menu, cant):
        self.items[menu] = self.items.get(menu, 0) + cant

    def quitar_item(self, menu, cant):
        if menu in self.items:
            self.items[menu] -= cant
            if self.items[menu] <= 0:
                del self.items[menu]

    def vaciar_pedido(self):
        self.items.clear()

    def subtotal(self):
        from crud.menu_crud import obtener_menu_por_nombre
        total = 0
        for m, c in self.items.items():
            menu_obj = obtener_menu_por_nombre(self.db, m) if self.db else None
            precio = menu_obj.precio if menu_obj else 0
            total += precio * c
        return total

    def iva(self):
        return round(self.subtotal() * IVA)

    def total(self):
        return self.subtotal() + self.iva()

    def _req_totales(self):
        from crud.menu_crud import obtener_menu_por_nombre, requerimientos_menu
        req = {}
        for m, c in self.items.items():
            menu_obj = obtener_menu_por_nombre(self.db, m) if self.db else None
            reqs = requerimientos_menu(self.db, menu_obj.id) if menu_obj else {}
            for ing, cant in reqs.items():
                req[ing] = req.get(ing, 0) + cant * c
        return req

    def confirmacion_req(self):
        return self.stock.validar_stock(self._req_totales())

    def stock_faltantes(self):
        return self.stock.faltantes(self._req_totales())

    def confirmar_y_desc(self):
        return self.stock.descontar(self._req_totales())

    def detalle(self):
        from crud.menu_crud import obtener_menu_por_nombre
        detalles = []
        for m, c in self.items.items():
            menu_obj = obtener_menu_por_nombre(self.db, m) if self.db else None
            precio = menu_obj.precio if menu_obj else 0
            detalles.append((m, c, precio, precio * c))
        return detalles
