from abc import ABC, abstractmethod

from .devolucion import Devolucion


class IRepositorioDeDevoluciones(ABC):
    @abstractmethod
    def obtener(self, folio) -> Devolucion: ...
    @abstractmethod
    def agregar(self, devolucion: Devolucion) -> None: ...
    @abstractmethod
    def guardar(self, devolucion: Devolucion) -> None: ...
