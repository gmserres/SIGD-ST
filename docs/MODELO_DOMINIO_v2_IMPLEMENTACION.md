# Modelo de Dominio SIGD-ST v2 — Lineamientos de implementación

## 1. Propósito

Este documento traduce el Modelo de Dominio v2 a lineamientos de
implementación sin definir reglas de negocio adicionales.

No constituye un plan de migración ni autoriza cambios sobre el sistema.

## 2. Alcance

Los lineamientos comprenden:

- Solicitud de Intervención;
- Decisión sobre la Intervención;
- Fondo Interviniente;
- Expediente;
- documentos;
- validaciones;
- historial;
- disposiciones;
- trazabilidad y consultas.

## 3. Entidad raíz

La Solicitud de Intervención deberá ser la entidad raíz de toda nueva
intervención administrativa.

El sistema deberá permitir registrarla sin que exista previamente una
Decisión sobre la Intervención, un Fondo Interviniente determinado o un
Expediente.

### Datos mínimos documentados

- `id_solicitud`
- `numero_solicitud`
- `procedencia`
- `id_suna`
- `fecha_ingreso`
- `establecimiento`
- `solicitante`
- `motivo`
- `prioridad`
- `estado`

Cuando la procedencia sea `SUNA`, `id_suna` será obligatorio. No se establecen
en este documento otros valores de procedencia ni reglas adicionales.

## 4. Decisión sobre la Intervención

La Decisión sobre la Intervención deberá vincularse de forma permanente con la
Solicitud de Intervención.

El análisis previo de la Solicitud forma parte del proceso de decisión y no
constituye una entidad administrativa autónoma. La actuación registrada es la
Decisión sobre la Intervención.

### Datos mínimos documentados

- `id_decision`
- `solicitud_intervencion_id`
- `fecha_decision`
- `autoridad_decisora`
- `resultado`
- `fundamento`
- `fondo_interviniente`
- `descripcion_fondo`
- `usuario_registrante`

Actualmente existen Solicitudes y Decisiones persistentes en PostgreSQL, así
como la creación de Expediente desde una Decisión aprobatoria de Fondo
Compensador. La creación requiere que la Decisión tenga un Fondo Interviniente
determinado. El alta directa de Expediente continúa disponible por
compatibilidad.

La determinación del Fondo Interviniente no deberá producirse implícitamente
durante el registro de la solicitud.

## 5. Fondo Interviniente

El Fondo Interviniente deberá representarse separadamente del procedimiento de
contratación.

Continúa pendiente decidir si su representación será:

- un catálogo institucional; o
- una entidad propia del dominio.

Hasta que esta decisión sea aprobada, no corresponde fijar una estructura
definitiva de almacenamiento ni comportamiento específico.

## 6. Expediente

El Expediente deberá:

- crearse como consecuencia de una Decisión sobre la Intervención;
- mantener una referencia permanente a la Solicitud de Intervención de origen;
- conservar sus relaciones actuales con documentos, validaciones, historial y
  disposiciones;
- poder coexistir durante la transición con expedientes creados bajo el modelo
  anterior.

No se define en este documento una regla automática para crear el expediente ni
una equivalencia entre sus estados actuales y los estados futuros de la
solicitud.

## 7. Separación de conceptos

La implementación deberá utilizar conceptos diferentes para:

- Fondo Interviniente: ámbito institucional que atiende la solicitud.
- Procedimiento de contratación: mecanismo administrativo utilizado en el
  trámite.

La selección o detección de uno no deberá determinar implícitamente el otro.

## 8. Trazabilidad

La implementación deberá permitir reconstruir:

```text
Solicitud de Intervención
→ Decisión sobre la Intervención
→ Fondo Interviniente
→ Expediente
→ Disposición
```

La trazabilidad deberá conservar:

- origen;
- decisiones;
- responsables;
- resultado de la intervención.

## 9. Consultas

La implementación deberá permitir localizar y recorrer la intervención por:

- número de solicitud;
- ID SUNA;
- expediente interno;
- expediente GDEBA;
- disposición.

Una consulta deberá permitir acceder a las relaciones administrativas
derivadas, sin considerar cada identificador como un registro aislado.

## 10. Compatibilidad con el modelo anterior

Los expedientes existentes deberán continuar siendo administrables durante la
transición.

La incorporación del Modelo de Dominio v2 no deberá interpretar
retroactivamente datos inexistentes ni inventar solicitudes, decisiones o
autoridades decisoras.

La estrategia para vincular expedientes anteriores con solicitudes deberá
definirse y aprobarse antes de ejecutar una migración de datos.

## 11. Correspondencia con componentes actuales

Actualmente se encuentran integrados Solicitudes, Decisiones, creación de
Expediente desde una Decisión aprobatoria, alta directa compatible de
Expedientes, Documentos, Checklist de existencia física, Configuración UC,
análisis de OP, Validaciones Administrativas y Disposiciones emitidas.

Solicitudes, Decisiones, Expedientes, Configuraciones UC y sus asociaciones,
metadatos documentales, checklists, Validaciones Administrativas y
Disposiciones emitidas poseen persistencia PostgreSQL. El análisis de OP se
calcula bajo demanda. La evolución del esquema se administra mediante las
migraciones Alembic incluidas en el repositorio.

Los metadatos y resultados administrativos se conservan en PostgreSQL; los
archivos cargados y documentos generados se almacenan en el filesystem. Los
borradores de Disposición y el historial operativo del Expediente permanecen
en memoria. El historial de la Solicitud puede reconstruirse desde la
Solicitud y sus Decisiones persistidas.

Su existencia no convierte al Expediente en entidad raíz ni autoriza a utilizar
`tipo_tramite` como reemplazo del Fondo Interviniente o del procedimiento de
contratación.

## 12. Decisiones funcionales y arquitectónicas pendientes

Requieren definición funcional o arquitectónica previa:

1. representación definitiva del Fondo Interviniente;
2. estados y transiciones de la Solicitud de Intervención;
3. condiciones para modificar una Decisión sobre la Intervención;
4. tratamiento de rectificaciones o reemplazos de decisiones;
5. estrategia de vinculación de expedientes preexistentes;
6. permisos asociados a operadores y autoridades decisoras.

Estas cuestiones no deberán resolverse mediante supuestos técnicos.

## 13. Restricciones de implementación

- No crear un expediente antes de la decisión administrativa en el nuevo flujo.
- No exigir Fondo Interviniente al registrar la solicitud.
- No representar Fondo Interviniente como sinónimo de procedimiento de
  contratación.
- No eliminar la compatibilidad con expedientes existentes durante la
  transición.
- No perder la trazabilidad entre entidades.
- No incorporar reglas de negocio que no estén documentadas y aprobadas.

## 14. Condición para migraciones futuras

Antes de realizar nuevas migraciones que afecten este modelo deberá existir un
plan aprobado que:

- identifique componentes afectados;
- ordene las fases;
- establezca compatibilidad;
- defina pruebas y rollback;
- preserve los datos y funcionalidades vigentes.
