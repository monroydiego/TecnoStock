"""Application Service: solo coordina. Las reglas viven en el dominio (sección 5 del informe)."""
from dataclasses import dataclass
from datetime import datetime

from ...dominio.apartados.apartado import Apartado
from ...dominio.apartados.conversion_de_apartado import ConversionDeApartado
from ...dominio.compartido.errores import ReglaDeNegocioViolada
from ...dominio.compartido.valores import Dinero, Folio
from ..resultado import Rechazo, Resultado, TraductorDeRechazos


@dataclass(frozen=True)
class ConfirmacionDeApartado:
    folio: Folio
    fecha_limite: datetime
    saldo_pendiente: Dinero


class ServicioDeApartados:
    def __init__(self, uow, apartados, unidades, productos, politicas, ventas, conversion: ConversionDeApartado,
                 reloj, folios, contexto, traductor=None):
        self._uow, self._apartados, self._unidades = uow, apartados, unidades
        self._productos, self._politicas, self._ventas = productos, politicas, ventas
        self._conversion, self._reloj, self._folios, self._contexto = conversion, reloj, folios, contexto
        self._traductor = traductor or TraductorDeRechazos()

    def apartar_producto(self, cmd) -> Resultado:                      # CU-01
        ahora = self._reloj.ahora()
        self._uow.iniciar()
        try:
            politica = self._politicas.obtener_politica_vigente()
            producto = self._productos.obtener(cmd.producto_id)
            unidad = self._unidades.obtener_unidad_disponible(cmd.producto_id, cmd.sucursal_id)
            folio = self._folios.siguiente("APT")
            apartado = Apartado.crear(folio, cmd.cliente_id, unidad, producto.precio_de_lista,
                                      cmd.anticipo, politica, ahora)
            unidad.apartar(apartado.folio, cmd.sucursal_id)
            self._apartados.agregar(apartado)
            self._unidades.guardar(unidad)
            self._uow.confirmar()
            return Resultado.exito(ConfirmacionDeApartado(folio, apartado.vigencia.hasta, apartado.saldo_pendiente()))
        except ReglaDeNegocioViolada as ex:
            self._uow.descartar()
            return Resultado.rechazar(self._traductor.traducir(ex))

    def convertir_apartado_en_venta(self, cmd) -> Resultado:           # CU-03
        ahora, cajero = self._reloj.ahora(), self._contexto.operador_actual()
        self._uow.iniciar()
        try:
            apartado = self._apartados.obtener(cmd.folio_de_apartado)
            unidad = self._unidades.obtener(apartado.unidad_id)
            producto = self._productos.obtener(unidad.producto_id)
            politica = self._politicas.obtener_politica_vigente()
            resultado = self._conversion.convertir(apartado, unidad, producto, cmd.pago_del_saldo,
                                                   cmd.serie_capturada, self._folios.siguiente("VTA"),
                                                   cajero, politica, ahora)
            if resultado.es_exitosa():
                self._ventas.agregar(resultado.venta)
            self._apartados.guardar(apartado)
            self._unidades.guardar(unidad)
            self._uow.confirmar()   # también confirma el rechazo con efecto (vencimiento)
            if resultado.es_exitosa():
                return Resultado.exito(resultado.venta.folio)
            return Resultado.rechazar(self._traductor.traducir(ReglaDeNegocioViolada(resultado.motivo,
                                      "El apartado venció; la unidad fue liberada")))
        except ReglaDeNegocioViolada as ex:
            self._uow.descartar()
            return Resultado.rechazar(self._traductor.traducir(ex))
