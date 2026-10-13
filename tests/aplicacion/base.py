import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from tecnostock.composicion import crear_aplicacion
from tecnostock.dominio.catalogo.producto import Producto
from tecnostock.dominio.compartido.valores import (CategoriaDeProducto as C, Dinero, MetodoDePago, NumeroDeSerie,
                                                   Operador, PagoRecibido, Rol)
from tecnostock.dominio.inventario.unidad_inventario import UnidadInventario

SUC = "SUC-01"
CEL = "PROD-CEL"
S1, S2 = NumeroDeSerie("SN-001"), NumeroDeSerie("SN-002")


def pago(monto, metodo=MetodoDePago.EFECTIVO):
    return PagoRecibido(metodo, Dinero.de(monto))


class BaseDeEscenarios(unittest.TestCase):
    """Escenario: un celular serializable ($10,000) con dos unidades disponibles en SUC-01."""

    def setUp(self):
        self.app = crear_aplicacion()
        self.app.productos.registrar(Producto(CEL, "CEL-1", "Celular", C.CELULARES, True, Dinero.de(10000)))
        for i, s in enumerate((S1, S2), 1):
            u = UnidadInventario(f"U{i}", CEL, SUC, s)
            self.app.almacen.datos["unidades"][u.id] = u

    def estado(self, unidad_id):
        return self.app.almacen.datos["unidades"][unidad_id].estado.value

    def como(self, rol):
        self.app.contexto.iniciar_sesion(Operador("u-" + rol.value, rol))
