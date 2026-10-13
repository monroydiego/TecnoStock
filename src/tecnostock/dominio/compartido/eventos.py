"""Eventos de dominio: hechos del negocio que ya ocurrieron."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .valores import Folio, UnidadId


class EventoDeDominio:
    pass


@dataclass(frozen=True)
class ApartadoCreado(EventoDeDominio):
    folio: Folio
    fecha_limite: datetime


@dataclass(frozen=True)
class ApartadoVencido(EventoDeDominio):
    folio: Folio
    unidad_id: UnidadId


@dataclass(frozen=True)
class VentaCerrada(EventoDeDominio):
    folio: Folio
    folio_de_apartado_origen: Optional[Folio] = None


@dataclass(frozen=True)
class DevolucionDerivadaASupervisor(EventoDeDominio):
    folio: Folio
    incumplimientos: tuple = ()


@dataclass(frozen=True)
class DevolucionAceptada(EventoDeDominio):
    folio: Folio
    unidad_id: UnidadId
    folio_de_venta: Folio


@dataclass(frozen=True)
class DevolucionRechazada(EventoDeDominio):
    folio: Folio
