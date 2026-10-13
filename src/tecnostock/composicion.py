"""Raíz de composición: ensambla dominio, aplicación e infraestructura."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .aplicacion.consultas.consultas import ConsultasDeDevoluciones, ConsultasDeInventario
from .aplicacion.eventos.manejadores import ManejadorDeAvisos, ManejadorDeComprobantes, ManejadorDeReingresoDeUnidades
from .aplicacion.servicios.servicio_de_apartados import ServicioDeApartados
from .aplicacion.servicios.servicio_de_devoluciones import ServicioDeDevoluciones
from .aplicacion.servicios.servicio_de_ventas import ServicioDeVentas
from .dominio.apartados.conversion_de_apartado import ConversionDeApartado
from .dominio.compartido.eventos import (ApartadoCreado, ApartadoVencido, DevolucionAceptada,
                                         DevolucionDerivadaASupervisor, VentaCerrada)
from .dominio.compartido.valores import CategoriaDeProducto as C, MetodoDePago, Operador, Rol
from .dominio.devoluciones.criterio import CriterioDeDevolucion, ReglaDeComprobanteVigente, ReglaDePlazoPorCategoria
from .dominio.politicas.politica_comercial import PoliticaComercial
from .infraestructura.persistencia_en_memoria import almacen as m
from .infraestructura.servicios.servicios import (ContextoDeUsuarioDeSesion, GeneradorDeFolios,
                                                  PublicadorDeEventosEnMemoria, RelojFijo)


@dataclass
class Aplicacion:
    apartados: ServicioDeApartados
    ventas: ServicioDeVentas
    devoluciones: ServicioDeDevoluciones
    consultas_inventario: ConsultasDeInventario
    consultas_devoluciones: ConsultasDeDevoluciones
    almacen: m.Almacen
    reloj: RelojFijo
    contexto: ContextoDeUsuarioDeSesion
    comprobantes: ManejadorDeComprobantes
    avisos: ManejadorDeAvisos
    productos: m.RepositorioDeProductosEnMemoria


def crear_aplicacion(ahora: datetime = datetime(2026, 10, 1, 10, 0)) -> Aplicacion:
    al = m.Almacen()
    pub = PublicadorDeEventosEnMemoria()
    uow = m.UnidadDeTrabajoEnMemoria(al, pub)
    apartados, unidades = m.RepositorioDeApartadosEnMemoria(al), m.RepositorioDeUnidadesEnMemoria(al)
    ventas, devs = m.RepositorioDeVentasEnMemoria(al), m.RepositorioDeDevolucionesEnMemoria(al)
    productos, politicas = m.RepositorioDeProductosEnMemoria(al), m.RepositorioDePoliticasEnMemoria(al)
    # Valores SUPUESTOS del BRD (20%-30%, 7 días, 15-30 días): configurables, pendientes de validar.
    criterio = CriterioDeDevolucion([ReglaDeComprobanteVigente(),
                                     ReglaDePlazoPorCategoria({C.COMPUTADORAS: 15, C.CELULARES: 15,
                                                               C.ACCESORIOS: 30, C.COMPONENTES: 30})])
    politicas.establecer(PoliticaComercial(Decimal("0.20"), 7,
                                           {MetodoDePago.EFECTIVO, MetodoDePago.TARJETA}, criterio))
    reloj, folios = RelojFijo(ahora), GeneradorDeFolios()
    ctx = ContextoDeUsuarioDeSesion(Operador("cajero1", Rol.CAJERO))
    comp, avisos = ManejadorDeComprobantes(), ManejadorDeAvisos()
    reingreso = ManejadorDeReingresoDeUnidades(uow, unidades)
    pub.suscribir(ApartadoCreado, comp.al_crearse_apartado)
    pub.suscribir(VentaCerrada, comp.al_cerrarse_venta)
    pub.suscribir(DevolucionAceptada, comp.al_aceptarse_devolucion)
    pub.suscribir(DevolucionAceptada, reingreso.al_aceptarse_devolucion)
    pub.suscribir(DevolucionDerivadaASupervisor, avisos.al_derivarse_devolucion)
    pub.suscribir(ApartadoVencido, avisos.al_vencerse_apartado)
    return Aplicacion(
        ServicioDeApartados(uow, apartados, unidades, productos, politicas, ventas, ConversionDeApartado(),
                            reloj, folios, ctx),
        ServicioDeVentas(uow, ventas, unidades, productos, politicas, reloj, folios, ctx),
        ServicioDeDevoluciones(uow, ventas, devs, productos, politicas, reloj, folios, ctx),
        ConsultasDeInventario(m.LectorDeInventarioEnMemoria(al)),
        ConsultasDeDevoluciones(m.LectorDeDevolucionesEnMemoria(al)),
        al, reloj, ctx, comp, avisos, productos)
