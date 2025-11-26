# logic/Stock.py
class Ingrediente:
    def __init__(self, nombre, unidad, cantidad):
        self.nombre = nombre
        self.unidad = unidad
        self.cantidad = cantidad

    def agregar(self, cant):
        self.cantidad += cant

    def descontar(self, cant):
        self.cantidad -= cant


class Stock:
    def __init__(self):
        self._items = {}  # nombre -> Ingrediente

    def agregar_o_sumar(self, nombre, unidad, cantidad):
        nombre = nombre.lower().strip()
        if nombre in self._items:
            self._items[nombre].agregar(cantidad)
        else:
            self._items[nombre] = Ingrediente(nombre, unidad, cantidad)

    def eliminar(self, nombre):
        nombre = nombre.lower().strip()
        if nombre in self._items:
            del self._items[nombre]

    def cantidad_de(self, nombre):
        nombre = nombre.lower().strip()
        if nombre in self._items:
            return self._items[nombre].cantidad
        return 0

    def listar(self):
        return list(self._items.values())

    def validar_stock(self, requerimientos):
        for ing, req in requerimientos.items():
            if ing.lower() not in self._items:
                return False
            if self._items[ing.lower()].cantidad < req:
                return False
        return True

    def faltantes(self, requerimientos):
        faltas = []
        for ing, req in requerimientos.items():
            disp = self._items.get(ing.lower())
            if not disp:
                faltas.append((ing, req, 0))
            elif disp.cantidad < req:
                faltas.append((ing, req, disp.cantidad))
        return faltas

    def descontar(self, requerimientos):
        if not self.validar_stock(requerimientos):
            return False
        for ing, req in requerimientos.items():
            self._items[ing.lower()].descontar(req)
        return True
