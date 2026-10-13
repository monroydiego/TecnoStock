from ...dominio.compartido.errores import ReglaDeNegocioViolada
from ...dominio.ventas.venta import LineaDeVenta, Venta
from ..resultado import Resultado, TraductorDeRechazos


class ServicioDeVentas:
    def __init__(self, uow, ventas, unidades, productos, politicas, reloj, folios, contexto, traductor=None):
        self._uow, self._ventas, self._unidades = uow, ventas, unidades
        self._productos, self._politicas = productos, politicas
        self._reloj, self._folios, self._contexto = reloj, folios, contexto
        self._traductor = traductor or TraductorDeRechazos()

    def registrar_venta(self, cmd) -> Resultado:                        # CU-02
        ahora, cajero = self._reloj.ahora(), self._contexto.operador_actual()
        self._uow.iniciar()
        try:
            politica = self._politicas.obtener_politica_vigente()
            folio = self._folios.siguiente("VTA")
            lineas = []
            for pedida in cmd.lineas:
                producto = self._productos.obtener(pedida.producto_id)
                unidad = self._unidades.obtener_unidad_para_venta(pedida.producto_id, cmd.sucursal_id,
                                                                  pedida.serie_capturada)
                unidad.vender(folio, cmd.sucursal_id)
                lineas.append(LineaDeVenta.crear(producto, unidad, pedida.serie_capturada, producto.precio_de_lista))
                self._unidades.guardar(unidad)
            venta = Venta.cerrar(folio, cmd.sucursal_id, cajero, lineas, cmd.pagos, politica, ahora)
            self._ventas.agregar(venta)
            self._uow.confirmar()
            return Resultado.exito(venta.folio)
        except ReglaDeNegocioViolada as ex:
            self._uow.descartar()
            return Resultado.rechazar(self._traductor.traducir(ex))
