"""Commands del lado de escritura (CQRS básico)."""
from dataclasses import dataclass
from typing import List, Optional

from ..dominio.compartido.valores import ClienteId, Folio, NumeroDeSerie, PagoRecibido, ProductoId, SucursalId


@dataclass(frozen=True)
class ApartarProductoCommand:
    producto_id: ProductoId
    sucursal_id: SucursalId
    cliente_id: ClienteId
    anticipo: PagoRecibido


@dataclass(frozen=True)
class ConvertirApartadoEnVentaCommand:
    folio_de_apartado: Folio
    pago_del_saldo: PagoRecibido
    serie_capturada: Optional[NumeroDeSerie] = None


@dataclass(frozen=True)
class LineaSolicitada:
    producto_id: ProductoId
    serie_capturada: Optional[NumeroDeSerie] = None


@dataclass(frozen=True)
class RegistrarVentaCommand:
    sucursal_id: SucursalId
    lineas: List[LineaSolicitada]
    pagos: List[PagoRecibido]


@dataclass(frozen=True)
class SolicitarDevolucionCommand:
    folio_de_venta: Folio
    producto_id: ProductoId
    motivo: "MotivoDeDevolucion"
    serie_capturada: Optional[NumeroDeSerie] = None


@dataclass(frozen=True)
class AutorizarDevolucionExcepcionalCommand:
    folio_de_devolucion: Folio
    autoriza: bool
    motivo: str


from ..dominio.devoluciones.devolucion import MotivoDeDevolucion  # noqa: E402  (para el tipo anterior)
