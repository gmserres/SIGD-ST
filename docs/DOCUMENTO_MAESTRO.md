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
→ Decisión sobre la Intervención
→ Fondo Interviniente
→ Expediente
→ Documentos
→ Validación
→ Disposición
→ Archivo
```

El Expediente no es la entidad raíz del dominio. Su creación es consecuencia
de una Decisión sobre la Intervención adoptada respecto de una Solicitud de
Intervención.

La Decisión sobre la Intervención registra la autoridad decisora, la fecha, el
resultado, el fundamento, el Fondo Interviniente cuando corresponda y el
usuario registrante.

## 4. Principios funcionales

1. Toda intervención administrativa comienza con una Solicitud de
   Intervención.
2. La solicitud puede registrarse antes de conocer el Fondo Interviniente.
3. La determinación del Fondo Interviniente es una decisión administrativa
   reservada a la autoridad competente.
4. Fondo Interviniente y procedimiento de contratación son conceptos
   diferentes y deben registrarse de forma independiente.
5. El vínculo entre solicitud, decisión, fondo, expediente y
   disposición debe conservarse permanentemente.
6. El análisis previo de la Solicitud forma parte del proceso de decisión y no
   constituye una entidad administrativa autónoma. La actuación registrada es
   la Decisión sobre la Intervención.
7. Los expedientes existentes deben poder continuar administrándose durante
   la transición al nuevo modelo.
8. Las reglas funcionales no documentadas requieren definición y aprobación
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

### Hito: Versión demostrable

**Estado: ALCANZADO**

Base funcional: **SIGD-ST — Fondo Compensador v1.0.0**.

Validaciones del hito:

- D1 — Escenario Oficial de Demostración: **APROBADO**.
- D2 — Paquete Demostrativo Reproducible: **APROBADO**.
- D3 — Ensayo General Institucional: **APROBADO**.

Dictamen: **VERSIÓN DEMOSTRABLE LISTA CON OBSERVACIONES**.

Bloqueantes funcionales: **NINGUNO**.

La demostración recorre la Mesa de Control, la Solicitud de Intervención, la
decisión administrativa, la relación Solicitud → Expediente —incluido el caso
1:N—, la próxima acción, el proveedor seleccionado, la preparación
administrativa, el checklist y la validación. También demuestra la
incorporación de una OP, el estado `PENDIENTE_REVALIDACION`, la revalidación,
el control Proveedor ↔ OP, los resultados `COINCIDE`, `HABILITADO` y
`CUIT_DIFERENTE`, la regularización explícita y el tratamiento de múltiples OP.
El circuito concluye con una Disposición por OP, generación de DOCX,
formalización, cierre, archivo y timeline durable.

Fuera del repositorio existe el paquete `SIGD_ST_DEMO_V1.zip`. Contiene sólo
datos y documentos ficticios, una base PostgreSQL y un storage aislados, los
checkpoints CP2, CP4, CP5 y CP7, restauración controlada, verificación mediante
los resultados `DEMO LISTA` y `DEMO NO LISTA`, protecciones contra el uso
accidental del entorno de desarrollo, manifests SHA-256 y una guía del
presentador. El ZIP, los dumps y sus storages no forman parte del repositorio.

Las siguientes observaciones son **NO BLOQUEANTES PARA LA VERSIÓN
DEMOSTRABLE**:

- ampliar las instrucciones de arranque de la demo;
- documentar los puertos esperados, sus posibles colisiones y la configuración
  del storage demo;
- mejorar la actualización visual inmediata después de determinadas
  mutaciones;
- reducir el scroll vertical del Expediente;
- mejorar la legibilidad secundaria para proyección;
- ampliar eventualmente la guía para un presentador que no conozca SIGD-ST.

“Versión demostrable” no significa “despliegue institucional productivo”. La
V1 demostrable permite presentar y validar funcionalmente el circuito. Para
una utilización institucional productiva permanecen fuera de este hito, entre
otros aspectos, la autenticación productiva, el despliegue institucional
definitivo, una estrategia operativa de backup y restauración, los
procedimientos institucionales, el procedimiento anual definitivo de UC y las
integraciones futuras con sistemas externos. Estos límites no constituyen
defectos de la versión demostrable.

## 7. Caminos posteriores posibles

El roadmap registra **VERSIÓN DEMOSTRABLE → ALCANZADA** y mantiene separados,
sin establecer todavía un próximo objetivo, estos caminos posibles:

1. presentación institucional;
2. preparación para uso institucional o productivo;
3. evolución funcional post-V1 o V1.1.

## 8. Decisiones pendientes

Permanece pendiente definir si el Fondo Interviniente será representado como:

- catálogo institucional; o
- entidad propia del dominio.

Hasta que exista una decisión funcional y arquitectónica aprobada, ninguna de
las dos alternativas se considera definitiva.

También deberán definirse antes de su implementación los estados, transiciones,
responsabilidades y reglas adicionales que no estén expresamente establecidos
en el Modelo de Dominio v2.

## 9. Control de cambios

Toda modificación funcional deberá:

1. identificar la regla o decisión afectada;
2. actualizar primero la documentación rectora correspondiente;
3. contar con aprobación previa;
4. mantener trazabilidad con la implementación posterior.
