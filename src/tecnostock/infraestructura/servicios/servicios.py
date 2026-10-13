from datetime import datetime
from typing import Callable, Dict, List

from ...aplicacion.puertos.puertos import IContextoDeUsuario, IGeneradorDeFolios, IPublicadorDeEventos, IReloj
from ...dominio.compartido.valores import Folio, Operador


class RelojDelSistema(IReloj):
    def ahora(self): return datetime.now()


class RelojFijo(IReloj):
    """Reloj controlable para probar vencimientos sin esperar días (principio D)."""

    def __init__(self, ahora: datetime): self._ahora = ahora
    def ahora(self): return self._ahora
    def fijar(self, ahora: datetime): self._ahora = ahora


class GeneradorDeFolios(IGeneradorDeFolios):
    def __init__(self): self._n: Dict[str, int] = {}

    def siguiente(self, tipo_de_operacion):
        self._n[tipo_de_operacion] = self._n.get(tipo_de_operacion, 0) + 1
        return Folio(f"{tipo_de_operacion}-{self._n[tipo_de_operacion]:06d}")


class ContextoDeUsuarioDeSesion(IContextoDeUsuario):
    def __init__(self, operador: Operador): self._op = operador
    def operador_actual(self): return self._op
    def iniciar_sesion(self, operador: Operador): self._op = operador


class PublicadorDeEventosEnMemoria(IPublicadorDeEventos):
    def __init__(self): self._suscriptores: Dict[type, List[Callable]] = {}

    def suscribir(self, tipo, manejador): self._suscriptores.setdefault(tipo, []).append(manejador)

    def publicar(self, eventos):
        for e in eventos:
            for m in self._suscriptores.get(type(e), []):
                m(e)
