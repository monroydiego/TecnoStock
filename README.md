# TecnoStock — Arquitectura de lógica de negocio (Unidad 3)

Repositorio de la actividad **Diseño arquitectural del sistema con IA** (curso Componentes de lógica de negocio).
Continúa el caso 05 de la Unidad 2 (BRD y User Stories de TecnoStock, retail de electrónica).

**Integrantes:** Eduardo Alejandro Acevedo Liuskos (2142139) · Emma Patricia Brown Sánchez (2135479) · Diego Monroy García (2135198)
**Profesor:** Miguel Ángel Gómez Marroquín

## Alcance
Proceso principal: **apartado, venta de unidades serializadas y devolución con autorización del Supervisor**.
Casos de uso diseñados: CU-01 Apartar producto · CU-02 Vender producto serializado · CU-03 Convertir apartado en venta ·
CU-04 Solicitar devolución · CU-05 Autorizar devolución excepcional.

## Decisiones principales
- **Domain Model** para los comandos; Transaction Script solo en lecturas (ADR-001).
- Aggregates: Apartado, UnidadInventario, Venta, Devolucion, PoliticaComercial y Producto (ADR-002).
- Service Layer + Unit of Work por caso de uso, eventos tras confirmar (ADR-003).
- CQRS básico sin base separada (ADR-004). Políticas parametrizables (ADR-005). Modelo de rechazo (ADR-006).
- Sin base de datos: repositorios y unidad de trabajo en memoria.

## Estructura
```
docs/            Informe, ADR, matriz de trazabilidad y bitácora de IA
diagrams/        fuente/ (.mmd Mermaid) y exportaciones/ (PNG/PDF de draw.io)
src/tecnostock/  dominio/ · aplicacion/ · infraestructura/ · composicion.py
tests/           dominio/ y aplicacion/ (los cinco casos de uso y sus rechazos)
```
La dependencia apunta siempre hacia el dominio: `infraestructura → aplicacion → dominio`.

## Cómo revisarlo
1. Leer `docs/01_informe_arquitectura/` (informe) y `docs/adr/`.
2. Abrir los diagramas de `diagrams/fuente/` en draw.io (Organizar → Insertar → Avanzado → Mermaid).
3. Ejecutar las pruebas (Python 3.9+, sin dependencias):
   ```
   ./run_tests.sh
   ```
4. Revisar `src/tecnostock/composicion.py` para ver cómo se ensamblan las capas.

## Supuestos pendientes de validar
Valores del BRD marcados como supuesto (anticipo 20%, vigencia 7 días, plazos de devolución 15/30 días, catálogo de métodos de pago)
están en `composicion.py` como configuración. Los hallazgos H-01 a H-08 están en el informe (sección 1.2).
