from datetime import timedelta

from tecnostock.aplicacion.comandos import (ApartarProductoCommand, AutorizarDevolucionExcepcionalCommand,
                                            ConvertirApartadoEnVentaCommand, LineaSolicitada, RegistrarVentaCommand,
                                            SolicitarDevolucionCommand)
from tecnostock.aplicacion.resultado import AlternativaSugerida as Alt
from tecnostock.dominio.compartido.errores import MotivoDeRechazo as M
from tecnostock.dominio.compartido.valores import MetodoDePago, Rol
from tecnostock.dominio.devoluciones.devolucion import EstadoDeDevolucion, MotivoDeDevolucion

from .base import CEL, S1, S2, SUC, BaseDeEscenarios, pago


class CU01_ApartarProducto(BaseDeEscenarios):
    def test_flujo_normal_bloquea_la_unidad_y_confirma_con_fecha_limite(self):
        r = self.app.apartados.apartar_producto(ApartarProductoCommand(CEL, SUC, "C1", pago(2000)))
        self.assertTrue(r.exitoso)
        self.assertEqual(r.valor.fecha_limite, self.app.reloj.ahora() + timedelta(days=7))
        self.assertEqual(self.estado("U1"), "Apartada")
        self.assertEqual(self.app.comprobantes.emitidos[0][0], "Apartado")  # evento tras confirmar

    def test_anticipo_insuficiente_se_rechaza_y_no_deja_cambios(self):
        r = self.app.apartados.apartar_producto(ApartarProductoCommand(CEL, SUC, "C1", pago(100)))
        self.assertFalse(r.exitoso)
        self.assertEqual(r.rechazo.motivo, M.ANTICIPO_INSUFICIENTE)
        self.assertEqual(self.estado("U1"), "Disponible")  # rollback

    def test_sin_existencia_sugiere_otras_sucursales(self):
        r = self.app.apartados.apartar_producto(ApartarProductoCommand(CEL, "SUC-09", "C1", pago(2000)))
        self.assertEqual(r.rechazo.alternativa, Alt.CONSULTAR_OTRAS_SUCURSALES)


class CU02_VenderSerializado(BaseDeEscenarios):
    def vender(self, serie, monto=10000):
        return self.app.ventas.registrar_venta(RegistrarVentaCommand(SUC, [LineaSolicitada(CEL, serie)], [pago(monto)]))

    def test_flujo_normal(self):
        r = self.vender(S1)
        self.assertTrue(r.exitoso)
        self.assertEqual(self.estado("U1"), "Vendida")

    def test_unidad_apartada_se_bloquea_y_ofrece_otra_unidad(self):
        self.app.apartados.apartar_producto(ApartarProductoCommand(CEL, SUC, "C1", pago(2000)))  # reserva U1
        r = self.vender(S1)
        self.assertEqual(r.rechazo.motivo, M.UNIDAD_APARTADA)
        self.assertEqual(r.rechazo.alternativa, Alt.ELEGIR_OTRA_UNIDAD)
        self.assertTrue(self.vender(S2).exitoso)  # el caso distinto: otra unidad

    def test_serie_obligatoria_en_producto_serializable(self):
        r = self.vender(None)
        self.assertEqual(r.rechazo.motivo, M.SERIE_REQUERIDA)
        self.assertEqual(self.estado("U1"), "Disponible")

    def test_metodo_de_pago_no_autorizado(self):
        r = self.app.ventas.registrar_venta(RegistrarVentaCommand(
            SUC, [LineaSolicitada(CEL, S1)], [pago(10000, MetodoDePago.TRANSFERENCIA)]))
        self.assertEqual(r.rechazo.motivo, M.METODO_DE_PAGO_NO_AUTORIZADO)


class CU03_ConvertirApartado(BaseDeEscenarios):
    def apartar(self):
        return self.app.apartados.apartar_producto(ApartarProductoCommand(CEL, SUC, "C1", pago(2000))).valor.folio

    def test_apartado_vigente_se_convierte_en_venta_con_el_anticipo(self):
        folio = self.apartar()
        r = self.app.apartados.convertir_apartado_en_venta(ConvertirApartadoEnVentaCommand(folio, pago(8000), S1))
        self.assertTrue(r.exitoso)
        self.assertEqual(self.estado("U1"), "Vendida")
        venta = self.app.almacen.datos["ventas"][r.valor]
        self.assertEqual(venta.folio_de_apartado_origen, folio)
        self.assertEqual(len(venta.pagos), 2)

    def test_apartado_vencido_se_rechaza_pero_el_vencimiento_se_guarda(self):
        folio = self.apartar()
        self.app.reloj.fijar(self.app.reloj.ahora() + timedelta(days=8))
        r = self.app.apartados.convertir_apartado_en_venta(ConvertirApartadoEnVentaCommand(folio, pago(8000), S1))
        self.assertEqual(r.rechazo.motivo, M.APARTADO_VENCIDO)
        self.assertEqual(r.rechazo.alternativa, Alt.INICIAR_VENTA_NUEVA)
        self.assertEqual(self.estado("U1"), "Disponible")  # rechazo con efecto
        self.assertEqual(self.app.almacen.datos["apartados"][folio].estado.value, "Vencido")
        self.assertEqual(self.app.avisos.enviados[0][0], "Vendedor")

    def test_saldo_insuficiente_hace_rollback_y_el_apartado_sigue_vigente(self):
        folio = self.apartar()
        r = self.app.apartados.convertir_apartado_en_venta(ConvertirApartadoEnVentaCommand(folio, pago(100), S1))
        self.assertEqual(r.rechazo.motivo, M.SALDO_INSUFICIENTE)
        self.assertEqual(self.app.almacen.datos["apartados"][folio].estado.value, "Vigente")

    def test_serie_distinta_a_la_apartada_se_rechaza(self):
        folio = self.apartar()
        r = self.app.apartados.convertir_apartado_en_venta(ConvertirApartadoEnVentaCommand(folio, pago(8000), S2))
        self.assertEqual(r.rechazo.motivo, M.SERIE_NO_COINCIDE)


class CU04_CU05_Devoluciones(BaseDeEscenarios):
    def vender(self):
        return self.app.ventas.registrar_venta(
            RegistrarVentaCommand(SUC, [LineaSolicitada(CEL, S1)], [pago(10000)])).valor

    def devolver(self, folio_venta):
        return self.app.devoluciones.solicitar_devolucion(
            SolicitarDevolucionCommand(folio_venta, CEL, MotivoDeDevolucion("Falla de fabrica"), S1))

    def test_dentro_de_plazo_se_acepta_y_la_unidad_se_reingresa_por_evento(self):
        folio = self.vender()
        r = self.devolver(folio)
        self.assertEqual(r.valor[1], EstadoDeDevolucion.ACEPTADA)
        self.assertEqual(self.estado("U1"), "Devuelta")

    def test_comprobante_inexistente_es_rechazo_definitivo(self):
        self.vender()
        from tecnostock.dominio.compartido.valores import Folio
        r = self.devolver(Folio("VTA-999999"))
        self.assertEqual(r.rechazo.motivo, M.COMPROBANTE_NO_VALIDO)
        self.assertEqual(self.app.almacen.datos["devoluciones"], {})

    def test_fuera_de_plazo_queda_en_revision_y_el_supervisor_autoriza(self):
        folio = self.vender()
        self.app.reloj.fijar(self.app.reloj.ahora() + timedelta(days=20))   # celulares: 15 días (supuesto)
        r = self.devolver(folio)
        self.assertEqual(r.valor[1], EstadoDeDevolucion.EN_REVISION)
        self.assertEqual(self.estado("U1"), "Vendida")
        self.assertEqual(self.app.avisos.enviados[0][0], "Supervisor")
        self.como(Rol.SUPERVISOR)
        a = self.app.devoluciones.autorizar_devolucion_excepcional(
            AutorizarDevolucionExcepcionalCommand(r.valor[0], True, "Cliente frecuente, falla comprobada"))
        self.assertEqual(a.valor, EstadoDeDevolucion.ACEPTADA)
        self.assertEqual(self.estado("U1"), "Devuelta")

    def test_solo_el_supervisor_puede_autorizar(self):
        folio = self.vender()
        self.app.reloj.fijar(self.app.reloj.ahora() + timedelta(days=20))
        r = self.devolver(folio)
        a = self.app.devoluciones.autorizar_devolucion_excepcional(
            AutorizarDevolucionExcepcionalCommand(r.valor[0], True, "intento del cajero"))
        self.assertEqual(a.rechazo.motivo, M.SOLO_SUPERVISOR_AUTORIZA)

    def test_el_supervisor_puede_denegar(self):
        folio = self.vender()
        self.app.reloj.fijar(self.app.reloj.ahora() + timedelta(days=20))
        r = self.devolver(folio)
        self.como(Rol.SUPERVISOR)
        a = self.app.devoluciones.autorizar_devolucion_excepcional(
            AutorizarDevolucionExcepcionalCommand(r.valor[0], False, "Sin evidencia de falla"))
        self.assertEqual(a.valor, EstadoDeDevolucion.RECHAZADA)
        self.assertEqual(self.estado("U1"), "Vendida")


class Consultas_CQRS(BaseDeEscenarios):
    def test_disponibilidad_en_sucursal_y_en_otras(self):
        q = self.app.consultas_inventario
        self.assertEqual(q.consultar_disponibilidad_en_sucursal(CEL, SUC).cantidad_disponible, 2)
        self.assertEqual(q.consultar_disponibilidad_en_otras_sucursales(CEL, "SUC-02")[0].cantidad_disponible, 2)

    def test_criterio_vigente(self):
        c = self.app.consultas_devoluciones.consultar_criterio_de_devolucion_vigente()
        self.assertEqual(c.plazo_por_categoria["Celulares"], 15)
