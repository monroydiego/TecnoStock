from abc import ABC, abstractmethod
from typing import Optional

from ..compartido.valores import NumeroDeSerie, ProductoId, SucursalId, UnidadId
from .unidad_inventario import UnidadInventario


class IRepositorioDeUnidades(ABC):
    """Contrato: lo que no existe lanza ReglaDeNegocioViolada (nunca devuelve None)."""

    @abstractmethod
    def obtener(self, unidad_id: UnidadId) -> UnidadInventario: ...
    @abstractmethod
    def obtener_por_serie(self, serie: NumeroDeSerie) -> UnidadInventario: ...
    @abstractmethod
    def obtener_unidad_disponible(self, producto_id: ProductoId, sucursal: SucursalId) -> UnidadInventario: ...
    @abstractmethod
    def obtener_unidad_para_venta(self, producto_id: ProductoId, sucursal: SucursalId,
                                  serie_capturada: Optional[NumeroDeSerie]) -> UnidadInventario: ...
    @abstractmethod
    def guardar(self, unidad: UnidadInventario) -> None: ...
