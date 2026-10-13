"""Manejadores de eventos: efectos secundarios tras confirmar la transacción (ADR-003)."""
from ...dominio.compartido.eventos import (ApartadoCreado, ApartadoVencido, DevolucionAceptada,
                                           DevolucionDerivadaASupervisor, VentaCerrada)


class ManejadorDeReingresoDeUnidades:
    """Transacción propia: la unidad devuelta pasa a 'Devuelta' (H-06)."""

    def __init__(self, uow, unidades):
        self._uow, self._unidades = uow, unidades

    def al_aceptarse_devolucion(self, evento: DevolucionAceptada) -> None:
        self._uow.iniciar()
        unidad = self._unidades.obtener(evento.unidad_id)
        unidad.registrar_devolucion(evento.folio)
        self._unidades.guardar(unidad)
        self._uow.confirmar()


class ManejadorDeComprobantes:
    def __init__(self):
        self.emitidos = []   # en la infraestructura real se imprimiría o generaría un PDF (US12)

    def al_crearse_apartado(self, e: ApartadoCreado): self.emitidos.append(("Apartado", e.folio))
    def al_cerrarse_venta(self, e: VentaCerrada): self.emitidos.append(("Venta", e.folio))
    def al_aceptarse_devolucion(self, e: DevolucionAceptada): self.emitidos.append(("Devolucion", e.folio))


class ManejadorDeAvisos:
    def __init__(self):
        self.enviados = []   # canal de notificación por validar con el stakeholder (US20)

    def al_derivarse_devolucion(self, e: DevolucionDerivadaASupervisor): self.enviados.append(("Supervisor", e.folio))
    def al_vencerse_apartado(self, e: ApartadoVencido): self.enviados.append(("Vendedor", e.folio))
