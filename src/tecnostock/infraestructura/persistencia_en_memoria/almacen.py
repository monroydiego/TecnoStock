"""Persistencia en memoria (sin base de datos por ahora). Repositorios, lectores y unidad de trabajo."""
import copy
from typing import Dict, List, Optional

from ...aplicacion.consultas.consultas import (CriterioDeDevolucionDto, DisponibilidadDeProductoDto,
                                               DisponibilidadPorSucursalDto, EstadoDeDevolucionDto,
                                               ILectorDeDevoluciones, ILectorDeInventario)
from ...aplicacion.puertos.puertos import IUnidadDeTrabajo
from ...dominio.apartados.repositorio import IRepositorioDeApartados
from ...dominio.catalogo.repositorio import IRepositorioDeProductos
from ...dominio.compartido.errores import MotivoDeRechazo as M, ReglaDeNegocioViolada
from ...dominio.devoluciones.repositorio import IRepositorioDeDevoluciones
from ...dominio.inventario.repositorio import IRepositorioDeUnidades
from ...dominio.inventario.unidad_inventario import EstadoDeUnidad
from ...dominio.politicas.politica_comercial import IRepositorioDePoliticas
from ...dominio.ventas.repositorio import IRepositorioDeVentas


class Almacen:
    def __init__(self):
        self.datos: Dict[str, dict] = {k: {} for k in ("apartados", "unidades", "ventas", "devoluciones", "productos")}
        self.politica = None
        self.tocados: List = []


def _no_encontrado(clave, m=M.NO_ENCONTRADO):
    return ReglaDeNegocioViolada(m, f"No se encontró {clave}")


class UnidadDeTrabajoEnMemoria(IUnidadDeTrabajo):
    def __init__(self, almacen: Almacen, publicador):
        self._a, self._pub, self._snapshot = almacen, publicador, None

    def iniciar(self):
        self._snapshot = copy.deepcopy(self._a.datos)
        self._a.tocados = []

    def confirmar(self):
        eventos = [e for raiz in self._a.tocados for e in raiz.extraer_eventos()]
        self._a.tocados, self._snapshot = [], None
        self._pub.publicar(eventos)          # solo tras confirmar

    def descartar(self):
        if self._snapshot is not None:
            self._a.datos.clear()
            self._a.datos.update(self._snapshot)
        self._a.tocados, self._snapshot = [], None


class _Base:
    def __init__(self, almacen: Almacen):
        self._a = almacen

    def _guardar(self, tabla, clave, obj):
        self._a.datos[tabla][clave] = obj
        self._a.tocados.append(obj)


class RepositorioDeApartadosEnMemoria(_Base, IRepositorioDeApartados):
    def obtener(self, folio):
        try:
            return self._a.datos["apartados"][folio]
        except KeyError:
            raise _no_encontrado(f"el apartado {folio.valor}")

    def agregar(self, apartado): self._guardar("apartados", apartado.folio, apartado)
    guardar = agregar


class RepositorioDeUnidadesEnMemoria(_Base, IRepositorioDeUnidades):
    def _todas(self): return list(self._a.datos["unidades"].values())

    def obtener(self, unidad_id):
        try:
            return self._a.datos["unidades"][unidad_id]
        except KeyError:
            raise _no_encontrado(f"la unidad {unidad_id}")

    def obtener_por_serie(self, serie):
        for u in self._todas():
            if u.serie == serie:
                return u
        raise _no_encontrado(f"la serie {serie.valor}")

    def obtener_unidad_disponible(self, producto_id, sucursal):
        for u in self._todas():
            if u.producto_id == producto_id and u.sucursal_actual == sucursal and u.estado is EstadoDeUnidad.DISPONIBLE:
                return u
        raise ReglaDeNegocioViolada(M.SIN_EXISTENCIA_DISPONIBLE, "No hay unidades disponibles en la sucursal")

    def obtener_unidad_para_venta(self, producto_id, sucursal, serie_capturada):
        if serie_capturada is not None:
            return self.obtener_por_serie(serie_capturada)
        return self.obtener_unidad_disponible(producto_id, sucursal)

    def guardar(self, unidad): self._guardar("unidades", unidad.id, unidad)


class RepositorioDeVentasEnMemoria(_Base, IRepositorioDeVentas):
    def obtener_por_folio(self, folio):
        try:
            return self._a.datos["ventas"][folio]
        except KeyError:
            raise ReglaDeNegocioViolada(M.COMPROBANTE_NO_VALIDO, "El comprobante de compra no existe")

    def agregar(self, venta): self._guardar("ventas", venta.folio, venta)


class RepositorioDeDevolucionesEnMemoria(_Base, IRepositorioDeDevoluciones):
    def obtener(self, folio):
        try:
            return self._a.datos["devoluciones"][folio]
        except KeyError:
            raise _no_encontrado(f"la devolución {folio.valor}")

    def agregar(self, d): self._guardar("devoluciones", d.folio, d)
    guardar = agregar


class RepositorioDeProductosEnMemoria(_Base, IRepositorioDeProductos):
    def obtener(self, producto_id):
        try:
            return self._a.datos["productos"][producto_id]
        except KeyError:
            raise _no_encontrado(f"el producto {producto_id}")

    def registrar(self, producto): self._a.datos["productos"][producto.id] = producto


class RepositorioDePoliticasEnMemoria(_Base, IRepositorioDePoliticas):
    def obtener_politica_vigente(self): return self._a.politica
    def establecer(self, politica): self._a.politica = politica


class LectorDeInventarioEnMemoria(_Base, ILectorDeInventario):
    def _disponibles(self, producto_id):
        return [u for u in self._a.datos["unidades"].values()
                if u.producto_id == producto_id and u.estado is EstadoDeUnidad.DISPONIBLE]

    def disponibilidad_en_sucursal(self, producto_id, sucursal):
        n = sum(1 for u in self._disponibles(producto_id) if u.sucursal_actual == sucursal)
        return DisponibilidadDeProductoDto(producto_id, sucursal, n)

    def disponibilidad_en_otras_sucursales(self, producto_id, sucursal_actual):
        por_sucursal: Dict[str, int] = {}
        for u in self._disponibles(producto_id):
            if u.sucursal_actual != sucursal_actual:
                por_sucursal[u.sucursal_actual] = por_sucursal.get(u.sucursal_actual, 0) + 1
        return [DisponibilidadPorSucursalDto(s, n) for s, n in por_sucursal.items()]


class LectorDeDevolucionesEnMemoria(_Base, ILectorDeDevoluciones):
    def estado_de_devolucion(self, folio):
        d = self._a.datos["devoluciones"].get(folio)
        if d is None:
            raise _no_encontrado(f"la devolución {folio.valor}")
        return EstadoDeDevolucionDto(folio.valor, d.estado.value, d.motivo.causal)

    def criterio_vigente(self):
        for regla in self._a.politica.criterio_de_devolucion_vigente().reglas:
            if hasattr(regla, "plazos"):
                return CriterioDeDevolucionDto({c.value: d for c, d in regla.plazos.items()})
        return CriterioDeDevolucionDto({})
