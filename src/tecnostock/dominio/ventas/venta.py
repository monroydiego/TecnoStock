from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..compartido.errores import MotivoDeRechazo as M, ReglaDeNegocioViolada
from ..compartido.eventos import VentaCerrada
from ..compartido.raiz import RaizDeAgregado
from ..compartido.valores import Dinero, Folio, NumeroDeSerie, Operador, PagoRecibido, ProductoId, SucursalId, UnidadId


@dataclass(frozen=True)
class LineaDeVenta:
    producto_id: ProductoId
    unidad_id: UnidadId
    serie: Optional[NumeroDeSerie]
    precio_unitario: Dinero

    @staticmethod
    def crear(producto, unidad, serie_capturada: Optional[NumeroDeSerie], precio: Dinero) -> "LineaDeVenta":
        if producto.requiere_serie and serie_capturada is None:  # RN-VTA-001
            raise ReglaDeNegocioViolada(M.SERIE_REQUERIDA, "El producto exige capturar el número de serie")
        return LineaDeVenta(producto.id, unidad.id, unidad.serie, precio)


class Venta(RaizDeAgregado):
    def __init__(self, folio, sucursal_id, cajero, lineas, pagos, fecha_de_cierre, folio_de_apartado_origen=None):
        super().__init__()
        self.folio, self.sucursal_id, self.cajero = folio, sucursal_id, cajero
        self.lineas: List[LineaDeVenta] = lineas
        self.pagos: List[PagoRecibido] = pagos
        self.fecha_de_cierre = fecha_de_cierre
        self.folio_de_apartado_origen = folio_de_apartado_origen

    @staticmethod
    def cerrar(folio: Folio, sucursal: SucursalId, cajero: Operador, lineas: List[LineaDeVenta],
               pagos: List[PagoRecibido], politica, ahora: datetime) -> "Venta":
        for p in pagos:
            politica.validar_metodo_de_pago(p.metodo)  # RN-VTA-002
        v = Venta(folio, sucursal, cajero, lineas, pagos, ahora)
        if v._pagado().es_menor_que(v.total()):
            raise ReglaDeNegocioViolada(M.SALDO_INSUFICIENTE, "Los pagos no cubren el total de la venta")
        v._registrar(VentaCerrada(folio))
        return v

    @staticmethod
    def cerrar_desde_apartado(folio, apartado, unidad, producto, pago_saldo, cajero, ahora) -> "Venta":
        linea = LineaDeVenta(producto.id, unidad.id, unidad.serie, apartado.precio_acordado)
        v = Venta(folio, apartado.sucursal_id, cajero, [linea], [apartado.anticipo, pago_saldo], ahora, apartado.folio)
        v._registrar(VentaCerrada(folio, apartado.folio))
        return v

    def total(self) -> Dinero:
        total = Dinero.de(0)
        for l in self.lineas:
            total = total.sumar(l.precio_unitario)
        return total

    def _pagado(self) -> Dinero:
        pagado = Dinero.de(0)
        for p in self.pagos:
            pagado = pagado.sumar(p.monto)
        return pagado

    def obtener_linea(self, producto_id: ProductoId, serie: Optional[NumeroDeSerie]) -> LineaDeVenta:
        for l in self.lineas:
            if l.producto_id == producto_id and (serie is None or l.serie == serie):
                return l
        raise ReglaDeNegocioViolada(M.LINEA_NO_PERTENECE_A_LA_VENTA, "El producto no corresponde a este comprobante")
