from abc import ABC, abstractmethod

from .apartado import Apartado


class IRepositorioDeApartados(ABC):
    @abstractmethod
    def obtener(self, folio) -> Apartado: ...
    @abstractmethod
    def agregar(self, apartado: Apartado) -> None: ...
    @abstractmethod
    def guardar(self, apartado: Apartado) -> None: ...
