"""Value Objects compartidos del dominio de TecnoStock."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

ProductoId = str
UnidadId = str
SucursalId = str
ClienteId = str


class Rol(Enum):
    VENDEDOR = "Vendedor"
    CAJERO = "Cajero"
    SUPERVISOR = "Supervisor"
    ALMACEN = "Almacen"


class MetodoDePago(Enum):
    # Catálogo oficial pendiente de validar con el stakeholder (RN-VTA-002).
    EFECTIVO = "Efectivo"
    TARJETA = "Tarjeta"
    TRANSFERENCIA = "Transferencia"


class CategoriaDeProducto(Enum):
    COMPUTADORAS = "Computadoras"
    CELULARES = "Celulares"
    ACCESORIOS = "Accesorios"
    COMPONENTES = "Componentes"


@dataclass(frozen=True)
class Dinero:
    monto: Decimal
    moneda: str = "MXN"

    @staticmethod
    def de(valor) -> "Dinero":
        return Dinero(Decimal(str(valor)))

    def sumar(self, otro: "Dinero") -> "Dinero":
        return Dinero(self.monto + otro.monto, self.moneda)

    def restar(self, otro: "Dinero") -> "Dinero":
        return Dinero(self.monto - otro.monto, self.moneda)

    def es_menor_que(self, otro: "Dinero") -> bool:
        return self.monto < otro.monto

    def porcentaje(self, factor: Decimal) -> "Dinero":
        return Dinero(self.monto * factor, self.moneda)


@dataclass(frozen=True)
class Folio:
    valor: str


@dataclass(frozen=True)
class NumeroDeSerie:
    valor: str


@dataclass(frozen=True)
class PagoRecibido:
    metodo: MetodoDePago
    monto: Dinero


@dataclass(frozen=True)
class Operador:
    usuario_id: str
    rol: Rol

    def es_supervisor(self) -> bool:
        return self.rol is Rol.SUPERVISOR
