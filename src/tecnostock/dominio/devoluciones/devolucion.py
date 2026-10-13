from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from ..compartido.errores import MotivoDeRechazo, ReglaDeNegocioViolada
from ..compartido.eventos import DevolucionAceptada, DevolucionDerivadaASupervisor, DevolucionRechazada
from ..compartido.raiz import RaizDeAgregado
from ..compartido.valores import Folio, NumeroDeSerie, Operador
from .criterio import DictamenDeDevolucion


class EstadoDeDevolucion(Enum):
    EN_REVISION = "EnRevision"
    ACEPTADA = "Aceptada"
    RECHAZADA = "Rechazada"


@dataclass(frozen=True)
class MotivoDeDevolucion:
    causal: str
    detalle: str = ""


@dataclass(frozen=True)
class DecisionDeSupervisor:
    """Autorización documentada (RN-SUP-002). Solo puede crearla un Supervisor."""
    supervisor: Operador
    autoriza: bool
    motivo: str
    fecha: datetime

    @staticmethod
    def registrar(operador: Operador, autoriza: bool, motivo: str, ahora: datetime) -> "DecisionDeSupervisor":
        if not operador.es_supervisor():
            raise ReglaDeNegocioViolada(MotivoDeRechazo.SOLO_SUPERVISOR_AUTORIZA,
                                        "Solo el Supervisor puede autorizar o denegar una devolución")
        return DecisionDeSupervisor(operador, autoriza, motivo, ahora)


class Devolucion(RaizDeAgregado):
    def __init__(self, folio, folio_de_venta, unidad_id, serie, motivo, dictamen, estado):
        super().__init__()
        self.folio, self.folio_de_venta = folio, folio_de_venta
        self.unidad_id, self.serie = unidad_id, serie
        self.motivo, self.dictamen, self.estado = motivo, dictamen, estado
        self.decision: Optional[DecisionDeSupervisor] = None

    @staticmethod
    def solicitar(folio: Folio, venta, producto_id: str, serie: Optional[NumeroDeSerie],
                  motivo: MotivoDeDevolucion, dictamen: DictamenDeDevolucion) -> "Devolucion":
        linea = venta.obtener_linea(producto_id, serie)
        estado = EstadoDeDevolucion.ACEPTADA if dictamen.cumple() else EstadoDeDevolucion.EN_REVISION
        d = Devolucion(folio, venta.folio, linea.unidad_id, linea.serie, motivo, dictamen, estado)
        if d.estado is EstadoDeDevolucion.ACEPTADA:
            d._registrar(DevolucionAceptada(folio, linea.unidad_id, venta.folio))
        else:
            d._registrar(DevolucionDerivadaASupervisor(folio, dictamen.incumplimientos()))
        return d

    def resolver(self, decision: DecisionDeSupervisor) -> None:
        if self.estado is not EstadoDeDevolucion.EN_REVISION:
            raise ReglaDeNegocioViolada(MotivoDeRechazo.TRANSICION_DE_ESTADO_INVALIDA,
                                        "Solo una devolución en revisión puede resolverse")
        self.decision = decision
        if decision.autoriza:
            self.estado = EstadoDeDevolucion.ACEPTADA
            self._registrar(DevolucionAceptada(self.folio, self.unidad_id, self.folio_de_venta))
        else:
            self.estado = EstadoDeDevolucion.RECHAZADA
            self._registrar(DevolucionRechazada(self.folio))
