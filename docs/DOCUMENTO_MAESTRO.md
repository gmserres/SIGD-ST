# Documento Maestro SIGD-ST

## 1. Propósito

Este documento establece la referencia funcional principal del Sistema
Inteligente de Gestión Documental para la Secretaría Técnica (SIGD-ST).

Su finalidad es ordenar la documentación vigente y evitar que el código, los
documentos históricos de sprint o las decisiones técnicas implícitas sean
interpretados como reglas de negocio no aprobadas.

## 2. Propósito del sistema

SIGD-ST administra intervenciones administrativas de la Secretaría Técnica
desde su ingreso hasta su resolución y archivo, conservando la trazabilidad de
las actuaciones y decisiones adoptadas.

## 3. Modelo de dominio vigente

El modelo funcional objetivo es el definido en
`docs/MODELO_DOMINIO_v2.md`.

La entidad raíz del dominio es la **Solicitud de Intervención**.

El flujo general documentado es:

```text
Solicitud de Intervención
→ Evaluación Administrativa
→ Decisión Administrativa
→ Fondo Interviniente
→ Expediente
→ Documentos
→ Validación
→ Disposición
→ Archivo
```

El Expediente no es la entidad raíz del dominio. Su creación es consecuencia
de una Decisión Administrativa adoptada respecto de una Solicitud de
Intervención.

## 4. Principios funcionales

1. Toda intervención administrativa comienza con una Solicitud de
   Intervención.
2. La solicitud puede registrarse antes de conocer el Fondo Interviniente.
3. La determinación del Fondo Interviniente es una decisión administrativa
   reservada a la autoridad competente.
4. Fondo Interviniente y procedimiento de contratación son conceptos
   diferentes y deben registrarse de forma independiente.
5. El vínculo entre solicitud, evaluación, decisión, fondo, expediente y
   disposición debe conservarse permanentemente.
6. Los expedientes existentes deben poder continuar administrándose durante
   la transición al nuevo modelo.
7. Las reglas funcionales no documentadas requieren definición y aprobación
   antes de implementarse.

## 5. Documentos normativos del proyecto

La documentación funcional se interpreta en el siguiente orden:

1. `docs/DOCUMENTO_MAESTRO.md`
2. `docs/MODELO_DOMINIO_v2.md`
3. `docs/MODELO_DOMINIO_v2_IMPLEMENTACION.md`
4. `docs/MODELO_DOMINIO.md`, como referencia del modelo anterior
5. Documentos de sprint y commit, como antecedentes históricos

Los documentos de sprint y commit describen la evolución del sistema, pero no
pueden introducir reglas de negocio que contradigan el Documento Maestro o el
Modelo de Dominio v2.

## 6. Estado de la implementación actual

La implementación existente corresponde al modelo anterior y está organizada
alrededor de Expediente.

Actualmente existen funcionalidades para:

- expedientes;
- documentos;
- proveedores y establecimientos;
- historial;
- checklist físico;
- análisis de órdenes de pago;
- validación;
- generación de disposiciones;
- parámetros institucionales.

La existencia de estas funcionalidades no modifica el modelo funcional
objetivo definido para la migración.

## 7. Decisiones pendientes

Permanece pendiente definir si el Fondo Interviniente será representado como:

- catálogo institucional; o
- entidad propia del dominio.

Hasta que exista una decisión funcional y arquitectónica aprobada, ninguna de
las dos alternativas se considera definitiva.

También deberán definirse antes de su implementación los estados, transiciones,
responsabilidades y reglas adicionales que no estén expresamente establecidos
en el Modelo de Dominio v2.

## 8. Control de cambios

Toda modificación funcional deberá:

1. identificar la regla o decisión afectada;
2. actualizar primero la documentación rectora correspondiente;
3. contar con aprobación previa;
4. mantener trazabilidad con la implementación posterior.
