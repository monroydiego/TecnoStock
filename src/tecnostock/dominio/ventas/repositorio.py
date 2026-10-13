from abc import ABC, abstractmethod

from .venta import Venta


class IRepositorioDeVentas(ABC):
    @abstractmethod
    def obtener_por_folio(self, folio) -> Venta: ...   # sin comprobante: ComprobanteNoValido (RN-DEV-001)
    @abstractmethod
    def agregar(self, venta: Venta) -> None: ...
