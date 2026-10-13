"""Errores de negocio expresados con el lenguaje ubicuo (ADR-006)."""
from enum import Enum


class MotivoDeRechazo(Enum):
    SIN_EXISTENCIA_DISPONIBLE = "SinExistenciaDisponible"
    UNIDAD_APARTADA = "UnidadApartada"
    UNIDAD_NO_DISPONIBLE = "UnidadNoDisponible"
    UNIDAD_EN_OTRA_SUCURSAL = "UnidadEnOtraSucursal"
    ANTICIPO_INSUFICIENTE = "AnticipoInsuficiente"
    METODO_DE_PAGO_NO_AUTORIZADO = "MetodoDePagoNoAutorizado"
    SERIE_REQUERIDA = "SerieRequerida"
    SERIE_NO_COINCIDE = "SerieNoCoincide"
    SALDO_INSUFICIENTE = "SaldoInsuficiente"
    APARTADO_VENCIDO = "ApartadoVencido"
    COMPROBANTE_NO_VALIDO = "ComprobanteNoValido"
    LINEA_NO_PERTENECE_A_LA_VENTA = "LineaNoPerteneceALaVenta"
    SOLO_SUPERVISOR_AUTORIZA = "SoloSupervisorAutoriza"
    TRANSICION_DE_ESTADO_INVALIDA = "TransicionDeEstadoInvalida"
    CONFLICTO_DE_CONCURRENCIA = "ConflictoDeConcurrencia"
    NO_ENCONTRADO = "NoEncontrado"


class ReglaDeNegocioViolada(Exception):
    def __init__(self, motivo: MotivoDeRechazo, mensaje: str = ""):
        super().__init__(mensaje or motivo.value)
        self.motivo = motivo
        self.mensaje_de_negocio = mensaje or motivo.value
