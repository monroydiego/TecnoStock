from __future__ import annotations
from enum import Enum
from typing import Optional

from ..compartido.errores import MotivoDeRechazo as M, ReglaDeNegocioViolada
from ..compartido.raiz import RaizDeAgregado
from ..compartido.valores import Folio, NumeroDeSerie, ProductoId, SucursalId, UnidadId


class EstadoDeUnidad(Enum):
    DISPONIBLE = "Disponible"
    APARTADA = "Apartada"
    VENDIDA = "Vendida"
    DEVUELTA = "Devuelta"      # provisional hasta resolver el hallazgo H-06
    EN_TRANSITO = "EnTransito"  # previsto para US18/US19


class UnidadInventario(RaizDeAgregado):
    """Pieza física con identidad (serie) y ciclo de vida."""

    def __init__(self, id: UnidadId, producto_id: ProductoId, sucursal_actual: SucursalId,
                 serie: Optional[NumeroDeSerie], estado: EstadoDeUnidad = EstadoDeUnidad.DISPONIBLE):
        super().__init__()
        self.id, self.producto_id, self.sucursal_actual = id, producto_id, sucursal_actual
        self.serie, self.estado = serie, estado
        self.folio_de_apartado_vigente: Optional[Folio] = None

    # -- comportamiento -------------------------------------------------
    def apartar(self, folio_apartado: Folio, sucursal: SucursalId) -> None:
        self._exigir_disponible_en(sucursal)
        self.estado = EstadoDeUnidad.APARTADA
        self.folio_de_apartado_vigente = folio_apartado

    def liberar_apartado(self, folio_apartado: Folio) -> None:
        if self.estado is not EstadoDeUnidad.APARTADA or self.folio_de_apartado_vigente != folio_apartado:
            raise ReglaDeNegocioViolada(M.TRANSICION_DE_ESTADO_INVALIDA, "La unidad no está apartada por ese folio")
        self.estado = EstadoDeUnidad.DISPONIBLE
        self.folio_de_apartado_vigente = None

    def vender(self, folio_venta: Folio, sucursal: SucursalId) -> None:
        self._exigir_disponible_en(sucursal)
        self.estado = EstadoDeUnidad.VENDIDA

    def vender_desde_apartado(self, folio_apartado: Folio, serie_capturada: Optional[NumeroDeSerie]) -> None:
        if self.estado is not EstadoDeUnidad.APARTADA or self.folio_de_apartado_vigente != folio_apartado:
            raise ReglaDeNegocioViolada(M.UNIDAD_NO_DISPONIBLE, "La unidad no está apartada por ese folio")
        if self.serie is not None and serie_capturada != self.serie:
            raise ReglaDeNegocioViolada(M.SERIE_NO_COINCIDE, "La serie capturada no es la de la unidad apartada")
        self.estado = EstadoDeUnidad.VENDIDA
        self.folio_de_apartado_vigente = None

    def registrar_devolucion(self, folio_devolucion: Folio) -> None:
        if self.estado is not EstadoDeUnidad.VENDIDA:
            raise ReglaDeNegocioViolada(M.TRANSICION_DE_ESTADO_INVALIDA, "Solo una unidad vendida puede devolverse")
        self.estado = EstadoDeUnidad.DEVUELTA

    # -- invariantes ----------------------------------------------------
    def _exigir_disponible_en(self, sucursal: SucursalId) -> None:
        if self.estado is EstadoDeUnidad.APARTADA:
            raise ReglaDeNegocioViolada(M.UNIDAD_APARTADA, "La unidad está apartada y vigente")
        if self.estado is not EstadoDeUnidad.DISPONIBLE:
            raise ReglaDeNegocioViolada(M.UNIDAD_NO_DISPONIBLE, f"La unidad está {self.estado.value}")
        if self.sucursal_actual != sucursal:
            raise ReglaDeNegocioViolada(M.UNIDAD_EN_OTRA_SUCURSAL, "La unidad está en otra sucursal")
