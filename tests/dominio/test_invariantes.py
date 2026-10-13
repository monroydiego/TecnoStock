import unittest

from tecnostock.dominio.compartido.errores import MotivoDeRechazo as M, ReglaDeNegocioViolada
from tecnostock.dominio.compartido.valores import Folio, NumeroDeSerie
from tecnostock.dominio.inventario.unidad_inventario import EstadoDeUnidad, UnidadInventario


class InvariantesDeUnidadInventario(unittest.TestCase):
    def setUp(self):
        self.u = UnidadInventario("U1", "P", "S1", NumeroDeSerie("X"))

    def test_una_unidad_apartada_no_se_vende(self):
        self.u.apartar(Folio("A1"), "S1")
        with self.assertRaises(ReglaDeNegocioViolada) as c:
            self.u.vender(Folio("V1"), "S1")
        self.assertEqual(c.exception.motivo, M.UNIDAD_APARTADA)

    def test_no_se_vende_desde_otra_sucursal(self):
        with self.assertRaises(ReglaDeNegocioViolada) as c:
            self.u.vender(Folio("V1"), "S2")
        self.assertEqual(c.exception.motivo, M.UNIDAD_EN_OTRA_SUCURSAL)

    def test_solo_una_unidad_vendida_se_devuelve(self):
        with self.assertRaises(ReglaDeNegocioViolada):
            self.u.registrar_devolucion(Folio("D1"))
        self.u.vender(Folio("V1"), "S1")
        self.u.registrar_devolucion(Folio("D1"))
        self.assertIs(self.u.estado, EstadoDeUnidad.DEVUELTA)

    def test_liberar_exige_el_mismo_folio(self):
        self.u.apartar(Folio("A1"), "S1")
        with self.assertRaises(ReglaDeNegocioViolada):
            self.u.liberar_apartado(Folio("OTRO"))
