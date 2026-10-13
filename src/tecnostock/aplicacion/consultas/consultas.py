"""Lado de lectura (CQRS básico): DTO propios, sin pasar por los aggregates."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class DisponibilidadDeProductoDto:
    producto: str
    sucursal: str
    cantidad_disponible: int


@dataclass(frozen=True)
class DisponibilidadPorSucursalDto:
    sucursal: str
    cantidad_disponible: int


@dataclass(frozen=True)
class EstadoDeDevolucionDto:
    folio: str
    estado: str
    motivo: str


@dataclass(frozen=True)
class CriterioDeDevolucionDto:
    plazo_por_categoria: Dict[str, int]


class ILectorDeInventario(ABC):
    @abstractmethod
    def disponibilidad_en_sucursal(self, producto_id, sucursal) -> DisponibilidadDeProductoDto: ...
    @abstractmethod
    def disponibilidad_en_otras_sucursales(self, producto_id, sucursal_actual) -> List[DisponibilidadPorSucursalDto]: ...


class ILectorDeDevoluciones(ABC):
    @abstractmethod
    def estado_de_devolucion(self, folio) -> EstadoDeDevolucionDto: ...
    @abstractmethod
    def criterio_vigente(self) -> CriterioDeDevolucionDto: ...


class ConsultasDeInventario:
    def __init__(self, lector: ILectorDeInventario):
        self._lector = lector

    def consultar_disponibilidad_en_sucursal(self, producto_id, sucursal_id):      # US04
        return self._lector.disponibilidad_en_sucursal(producto_id, sucursal_id)

    def consultar_disponibilidad_en_otras_sucursales(self, producto_id, sucursal_actual):  # US05
        return self._lector.disponibilidad_en_otras_sucursales(producto_id, sucursal_actual)


class ConsultasDeDevoluciones:
    def __init__(self, lector: ILectorDeDevoluciones):
        self._lector = lector

    def consultar_estado_de_devolucion(self, folio):                                # US02
        return self._lector.estado_de_devolucion(folio)

    def consultar_criterio_de_devolucion_vigente(self):                             # US16
        return self._lector.criterio_vigente()
