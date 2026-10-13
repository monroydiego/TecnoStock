from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..compartido.errores import MotivoDeRechazo as M, ReglaDeNegocioViolada
from ..compartido.eventos import ApartadoCreado, ApartadoVencido
from ..compartido.raiz import RaizDeAgregado
from ..compartido.valores import ClienteId, Dinero, Folio, PagoRecibido, SucursalId


class EstadoDeApartado(Enum):
    VIGENTE = "Vigente"
    CONVERTIDO = "Convertido"
    VENCIDO = "Vencido"
    CANCELADO = "Cancelado"


@dataclass(frozen=True)
class VigenciaDeApartado:
    desde: datetime
    hasta: datetime

    def ha_vencido(self, ahora: datetime) -> bool:
        return ahora > self.hasta


class Apartado(RaizDeAgregado):
    def __init__(self, folio, cliente_id, sucursal_id, unidad_id, precio_acordado, anticipo, vigencia):
        super().__init__()
        self.folio, self.cliente_id, self.sucursal_id, self.unidad_id = folio, cliente_id, sucursal_id, unidad_id
        self.precio_acordado, self.anticipo, self.vigencia = precio_acordado, anticipo, vigencia
        self.estado = EstadoDeApartado.VIGENTE

    @staticmethod
    def crear(folio: Folio, cliente_id: ClienteId, unidad, precio: Dinero, anticipo: PagoRecibido,
              politica, ahora: datetime) -> "Apartado":
        politica.validar_metodo_de_pago(anticipo.metodo)                       # RN-VTA-002
        if anticipo.monto.es_menor_que(politica.anticipo_minimo_sobre(precio)):  # RN-APT-001*
            raise ReglaDeNegocioViolada(M.ANTICIPO_INSUFICIENTE, "El anticipo es menor al mínimo de la política")
        limite = politica.fecha_limite_desde(ahora)                              # RN-APT-002*
        a = Apartado(folio, cliente_id, unidad.sucursal_actual, unidad.id, precio, anticipo,
                     VigenciaDeApartado(ahora, limite))
        a._registrar(ApartadoCreado(folio, limite))
        return a

    def esta_vigente(self, ahora: datetime) -> bool:
        return self.estado is EstadoDeApartado.VIGENTE and not self.vigencia.ha_vencido(ahora)

    def saldo_pendiente(self) -> Dinero:
        return self.precio_acordado.restar(self.anticipo.monto)

    def liquidar(self, pago_saldo: PagoRecibido, politica, ahora: datetime) -> None:
        if not self.esta_vigente(ahora):
            raise ReglaDeNegocioViolada(M.TRANSICION_DE_ESTADO_INVALIDA, "Solo un apartado vigente puede liquidarse")
        politica.validar_metodo_de_pago(pago_saldo.metodo)
        if pago_saldo.monto.es_menor_que(self.saldo_pendiente()):
            raise ReglaDeNegocioViolada(M.SALDO_INSUFICIENTE, "El pago no cubre el saldo pendiente (H-04)")
        self.estado = EstadoDeApartado.CONVERTIDO

    def vencer(self, ahora: datetime) -> None:
        if self.estado is not EstadoDeApartado.VIGENTE:
            raise ReglaDeNegocioViolada(M.TRANSICION_DE_ESTADO_INVALIDA, "Solo un apartado vigente puede vencer")
        self.estado = EstadoDeApartado.VENCIDO
        self._registrar(ApartadoVencido(self.folio, self.unidad_id))

    def cancelar(self, decision) -> None:  # US14, fuera de los cinco casos de uso
        if self.estado is not EstadoDeApartado.VIGENTE or not decision.autoriza:
            raise ReglaDeNegocioViolada(M.TRANSICION_DE_ESTADO_INVALIDA, "No se puede cancelar el apartado")
        self.estado = EstadoDeApartado.CANCELADO
