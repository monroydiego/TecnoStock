"""Servicio de dominio: coordina Apartado, UnidadInventario y Venta (ADR-002, ADR-006)."""
from dataclasses import dataclass
from typing import Optional

from ..compartido.errores import MotivoDeRechazo
from ..ventas.venta import Venta


@dataclass(frozen=True)
class ResultadoDeConversion:
    venta: Optional[Venta] = None
    motivo: Optional[MotivoDeRechazo] = None

    def es_exitosa(self) -> bool:
        return self.venta is not None


class ConversionDeApartado:
    def convertir(self, apartado, unidad, producto, pago_saldo, serie_capturada, folio_venta,
                  cajero, politica, ahora) -> ResultadoDeConversion:
        if not apartado.esta_vigente(ahora):
            # Rechazo con efecto: el vencimiento y la liberación de la unidad sí se guardan.
            apartado.vencer(ahora)
            unidad.liberar_apartado(apartado.folio)
            return ResultadoDeConversion(motivo=MotivoDeRechazo.APARTADO_VENCIDO)
        apartado.liquidar(pago_saldo, politica, ahora)
        unidad.vender_desde_apartado(apartado.folio, serie_capturada)
        venta = Venta.cerrar_desde_apartado(folio_venta, apartado, unidad, producto, pago_saldo, cajero, ahora)
        return ResultadoDeConversion(venta=venta)
