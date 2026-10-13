"""Resultado de una operación y traducción de rechazos de negocio (ADR-006)."""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from ..dominio.compartido.errores import MotivoDeRechazo as M, ReglaDeNegocioViolada


class AlternativaSugerida(Enum):
    NINGUNA = "Ninguna"
    CONSULTAR_OTRAS_SUCURSALES = "ConsultarOtrasSucursales"
    ELEGIR_OTRA_UNIDAD = "ElegirOtraUnidad"
    CAPTURAR_SERIE = "CapturarSerie"
    INICIAR_VENTA_NUEVA = "IniciarVentaNueva"
    DERIVAR_A_SUPERVISOR = "DerivarASupervisor"


@dataclass(frozen=True)
class Rechazo:
    motivo: M
    mensaje_de_negocio: str
    alternativa: AlternativaSugerida = AlternativaSugerida.NINGUNA


@dataclass(frozen=True)
class Resultado:
    exitoso: bool
    valor: Any = None
    rechazo: Optional[Rechazo] = None

    @staticmethod
    def exito(valor=None) -> "Resultado":
        return Resultado(True, valor)

    @staticmethod
    def rechazar(rechazo: Rechazo) -> "Resultado":
        return Resultado(False, None, rechazo)


_ALTERNATIVAS = {
    M.SIN_EXISTENCIA_DISPONIBLE: AlternativaSugerida.CONSULTAR_OTRAS_SUCURSALES,
    M.UNIDAD_APARTADA: AlternativaSugerida.ELEGIR_OTRA_UNIDAD,
    M.SERIE_REQUERIDA: AlternativaSugerida.CAPTURAR_SERIE,
    M.APARTADO_VENCIDO: AlternativaSugerida.INICIAR_VENTA_NUEVA,
}


class TraductorDeRechazos:
    def traducir(self, ex: ReglaDeNegocioViolada) -> Rechazo:
        return Rechazo(ex.motivo, ex.mensaje_de_negocio, _ALTERNATIVAS.get(ex.motivo, AlternativaSugerida.NINGUNA))
