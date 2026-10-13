"""Criterio de devolución: lista de reglas intercambiables (principio O, ADR-005)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

from ..compartido.valores import CategoriaDeProducto


@dataclass(frozen=True)
class ResultadoDeRegla:
    cumple: bool
    razon: str = ""


class ReglaDeDevolucion(ABC):
    @abstractmethod
    def evaluar(self, venta, linea, producto, ahora: datetime) -> ResultadoDeRegla: ...


class ReglaDeComprobanteVigente(ReglaDeDevolucion):
    """RN-DEV-001: el comprobante existe y la línea le pertenece (ya verificado al obtener la venta)."""

    def evaluar(self, venta, linea, producto, ahora):
        if ahora < venta.fecha_de_cierre:
            return ResultadoDeRegla(False, "El comprobante tiene fecha posterior a la solicitud")
        return ResultadoDeRegla(True)


class ReglaDePlazoPorCategoria(ReglaDeDevolucion):
    """RN-DEV-002*: plazo máximo en días naturales por categoría (valores configurables)."""

    def __init__(self, plazo_en_dias_por_categoria: Dict[CategoriaDeProducto, int]):
        self.plazos = plazo_en_dias_por_categoria

    def evaluar(self, venta, linea, producto, ahora):
        plazo = self.plazos[producto.categoria]
        dias = (ahora - venta.fecha_de_cierre).days
        if dias > plazo:
            return ResultadoDeRegla(False, f"Fuera de plazo: {dias} días, máximo {plazo}")
        return ResultadoDeRegla(True)


@dataclass(frozen=True)
class DictamenDeDevolucion:
    resultados: Tuple[ResultadoDeRegla, ...]

    def cumple(self) -> bool:
        return all(r.cumple for r in self.resultados)

    def incumplimientos(self) -> Tuple[str, ...]:
        return tuple(r.razon for r in self.resultados if not r.cumple)


class CriterioDeDevolucion:
    def __init__(self, reglas: List[ReglaDeDevolucion]):
        self.reglas = reglas

    def evaluar(self, venta, linea, producto, ahora) -> DictamenDeDevolucion:
        return DictamenDeDevolucion(tuple(r.evaluar(venta, linea, producto, ahora) for r in self.reglas))
