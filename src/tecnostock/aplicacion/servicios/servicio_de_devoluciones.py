from ...dominio.compartido.errores import ReglaDeNegocioViolada
from ...dominio.devoluciones.devolucion import DecisionDeSupervisor, Devolucion
from ..resultado import Resultado, TraductorDeRechazos


class ServicioDeDevoluciones:
    def __init__(self, uow, ventas, devoluciones, productos, politicas, reloj, folios, contexto, traductor=None):
        self._uow, self._ventas, self._devoluciones = uow, ventas, devoluciones
        self._productos, self._politicas = productos, politicas
        self._reloj, self._folios, self._contexto = reloj, folios, contexto
        self._traductor = traductor or TraductorDeRechazos()

    def solicitar_devolucion(self, cmd) -> Resultado:                   # CU-04
        ahora = self._reloj.ahora()
        self._uow.iniciar()
        try:
            venta = self._ventas.obtener_por_folio(cmd.folio_de_venta)
            producto = self._productos.obtener(cmd.producto_id)
            criterio = self._politicas.obtener_politica_vigente().criterio_de_devolucion_vigente()
            linea = venta.obtener_linea(cmd.producto_id, cmd.serie_capturada)
            dictamen = criterio.evaluar(venta, linea, producto, ahora)
            devolucion = Devolucion.solicitar(self._folios.siguiente("DEV"), venta, cmd.producto_id,
                                              cmd.serie_capturada, cmd.motivo, dictamen)
            self._devoluciones.agregar(devolucion)
            self._uow.confirmar()
            return Resultado.exito((devolucion.folio, devolucion.estado))
        except ReglaDeNegocioViolada as ex:
            self._uow.descartar()
            return Resultado.rechazar(self._traductor.traducir(ex))

    def autorizar_devolucion_excepcional(self, cmd) -> Resultado:       # CU-05
        ahora, operador = self._reloj.ahora(), self._contexto.operador_actual()
        self._uow.iniciar()
        try:
            devolucion = self._devoluciones.obtener(cmd.folio_de_devolucion)
            decision = DecisionDeSupervisor.registrar(operador, cmd.autoriza, cmd.motivo, ahora)
            devolucion.resolver(decision)
            self._devoluciones.guardar(devolucion)
            self._uow.confirmar()
            return Resultado.exito(devolucion.estado)
        except ReglaDeNegocioViolada as ex:
            self._uow.descartar()
            return Resultado.rechazar(self._traductor.traducir(ex))
