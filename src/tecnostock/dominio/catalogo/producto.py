from dataclasses import dataclass

from ..compartido.raiz import RaizDeAgregado
from ..compartido.valores import CategoriaDeProducto, Dinero, ProductoId


class Producto(RaizDeAgregado):
    """Aggregate de referencia (catálogo)."""

    def __init__(self, id: ProductoId, sku: str, nombre: str, categoria: CategoriaDeProducto,
                 requiere_serie: bool, precio_de_lista: Dinero):
        super().__init__()
        self.id, self.sku, self.nombre = id, sku, nombre
        self.categoria, self.requiere_serie, self.precio_de_lista = categoria, requiere_serie, precio_de_lista
