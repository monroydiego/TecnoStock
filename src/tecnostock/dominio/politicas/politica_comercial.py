from datetime import datetime, timedelta
from decimal import Decimal
from typing import Set

from ..compartido.errores import MotivoDeRechazo, ReglaDeNegocioViolada
from ..compartido.raiz import RaizDeAgregado
from ..compartido.valores import Dinero, MetodoDePago
from ..devoluciones.criterio import CriterioDeDevolucion


class PoliticaComercial(RaizDeAgregado):
    """Valores vigentes. Los de rango en el BRD (20%-30%, 7 días, 15-30 días) son supuestos configurables."""

    def __init__(self, porcentaje_de_anticipo_minimo: Decimal, plazo_de_apartado_en_dias: int,
                 metodos_autorizados: Set[MetodoDePago], criterio_de_devolucion: CriterioDeDevolucion):
        super().__init__()
        self.porcentaje_de_anticipo_minimo = porcentaje_de_anticipo_minimo
        self.plazo_de_apartado_en_dias = plazo_de_apartado_en_dias
        self.metodos_autorizados = metodos_autorizados
        self.criterio_de_devolucion = criterio_de_devolucion

    def anticipo_minimo_sobre(self, precio: Dinero) -> Dinero:
        return precio.porcentaje(self.porcentaje_de_anticipo_minimo)

    def fecha_limite_desde(self, ahora: datetime) -> datetime:
        return ahora + timedelta(days=self.plazo_de_apartado_en_dias)

    def validar_metodo_de_pago(self, metodo: MetodoDePago) -> None:
        if metodo not in self.metodos_autorizados:
            raise ReglaDeNegocioViolada(MotivoDeRechazo.METODO_DE_PAGO_NO_AUTORIZADO,
                                        f"El método {metodo.value} no está autorizado")

    def criterio_de_devolucion_vigente(self) -> CriterioDeDevolucion:
        return self.criterio_de_devolucion


class IRepositorioDePoliticas:
    def obtener_politica_vigente(self) -> PoliticaComercial:
        raise NotImplementedError
