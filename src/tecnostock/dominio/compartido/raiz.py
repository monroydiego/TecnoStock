from typing import List

from .eventos import EventoDeDominio


class RaizDeAgregado:
    """Base de los aggregates: versión (concurrencia optimista) y eventos pendientes."""

    def __init__(self) -> None:
        self.version = 0
        self._eventos: List[EventoDeDominio] = []

    def _registrar(self, evento: EventoDeDominio) -> None:
        self._eventos.append(evento)

    def extraer_eventos(self) -> List[EventoDeDominio]:
        eventos, self._eventos = self._eventos, []
        return eventos
