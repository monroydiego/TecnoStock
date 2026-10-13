from abc import ABC, abstractmethod

from .producto import Producto


class IRepositorioDeProductos(ABC):
    @abstractmethod
    def obtener(self, producto_id) -> Producto: ...
