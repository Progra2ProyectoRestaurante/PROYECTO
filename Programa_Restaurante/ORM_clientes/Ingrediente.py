# Ingrediente.py
from dataclasses import dataclass

@dataclass
class Ingrediente:
    nombre: str
    unidad: str
    cantidad: float

    def agregar(self, cantidad: float):
        """Suma cantidad al stock del ingrediente."""
        self.cantidad += cantidad

    def descontar(self, cantidad: float) -> bool:
        """Descuenta si hay suficiente stock."""
        if cantidad <= self.cantidad:
            self.cantidad -= cantidad
            return True
        return False


