"""Puertos de la capa de aplicación (principio D). Las implementaciones viven en infraestructura."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from ...dominio.compartido.valores import Folio, Operador


class IUnidadDeTrabajo(ABC):
    @abstractmethod
    def iniciar(self) -> None: ...
    @abstractmethod
    def confirmar(self) -> None: ...
    @abstractmethod
    def descartar(self) -> None: ...


class IReloj(ABC):
    @abstractmethod
    def ahora(self) -> datetime: ...


class IGeneradorDeFolios(ABC):
    @abstractmethod
    def siguiente(self, tipo_de_operacion: str) -> Folio: ...


class IContextoDeUsuario(ABC):
    @abstractmethod
    def operador_actual(self) -> Operador: ...


class IPublicadorDeEventos(ABC):
    @abstractmethod
    def publicar(self, eventos: List) -> None: ...
