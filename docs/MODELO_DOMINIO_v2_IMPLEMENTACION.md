# Modelo de Dominio SIGD-ST v2 — Lineamientos de implementación

## 1. Propósito

Este documento traduce el Modelo de Dominio v2 a lineamientos de
implementación sin definir reglas de negocio adicionales.

No constituye un plan de migración ni autoriza cambios sobre el sistema.

## 2. Alcance

Los lineamientos comprenden:

- Solicitud de Intervención;
- Evaluación Administrativa;
- Decisión Administrativa;
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

El sistema deberá permitir registrarla sin que exista previamente:

- una Evaluación Administrativa;
- una Decisión Administrativa;
- un Fondo Interviniente determinado;
- un Expediente.

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

## 4. Evaluación Administrativa

La Evaluación Administrativa deberá vincularse con la Solicitud de
Intervención correspondiente.

Deberá permitir conservar las consultas, análisis, antecedentes y
verificaciones que sean registrados durante la etapa previa a la decisión.

Los tipos de evaluación, sus campos obligatorios, estados y reglas de cierre
permanecen pendientes de definición funcional.

## 5. Decisión Administrativa

La Decisión Administrativa deberá vincularse de forma permanente con la
Solicitud de Intervención.

### Datos mínimos documentados

- `solicitud_intervencion_id`
- `fondo_interviniente`
- `autoridad_decisora`
- `fecha_decision`
- `fundamento`
- `observaciones`

La determinación del Fondo Interviniente no deberá producirse implícitamente
durante el registro de la solicitud.

## 6. Fondo Interviniente

El Fondo Interviniente deberá representarse separadamente del procedimiento de
contratación.

Continúa pendiente decidir si su representación será:

- un catálogo institucional; o
- una entidad propia del dominio.

Hasta que esta decisión sea aprobada, no corresponde fijar una estructura
definitiva de almacenamiento ni comportamiento específico.

## 7. Expediente

El Expediente deberá:

- crearse como consecuencia de una Decisión Administrativa;
- mantener una referencia permanente a la Solicitud de Intervención de origen;
- conservar sus relaciones actuales con documentos, validaciones, historial y
  disposiciones;
- poder coexistir durante la transición con expedientes creados bajo el modelo
  anterior.

No se define en este documento una regla automática para crear el expediente ni
una equivalencia entre sus estados actuales y los estados futuros de la
solicitud.

## 8. Separación de conceptos

La implementación deberá utilizar conceptos diferentes para:

- Fondo Interviniente: ámbito institucional que atiende la solicitud.
- Procedimiento de contratación: mecanismo administrativo utilizado en el
  trámite.

La selección o detección de uno no deberá determinar implícitamente el otro.

## 9. Trazabilidad

La implementación deberá permitir reconstruir:

```text
Solicitud de Intervención
→ Evaluación Administrativa
→ Decisión Administrativa
→ Fondo Interviniente
→ Expediente
→ Disposición
```

La trazabilidad deberá conservar:

- origen;
- evaluaciones;
- decisiones;
- responsables;
- resultado de la intervención.

## 10. Consultas

La implementación deberá permitir localizar y recorrer la intervención por:

- número de solicitud;
- ID SUNA;
- expediente interno;
- expediente GDEBA;
- disposición.

Una consulta deberá permitir acceder a las relaciones administrativas
derivadas, sin considerar cada identificador como un registro aislado.

## 11. Compatibilidad con el modelo anterior

Los expedientes existentes deberán continuar siendo administrables durante la
transición.

La incorporación del Modelo de Dominio v2 no deberá interpretar
retroactivamente datos inexistentes ni inventar solicitudes, evaluaciones,
decisiones o autoridades decisoras.

La estrategia para vincular expedientes anteriores con solicitudes deberá
definirse y aprobarse antes de ejecutar una migración de datos.

## 12. Correspondencia con componentes actuales

Los componentes actuales relacionados con expedientes, documentos, historial,
validación, análisis de OP y disposiciones representan funcionalidades
existentes que deberán evaluarse dentro del nuevo flujo.

Su existencia no convierte al Expediente en entidad raíz ni autoriza a utilizar
`tipo_tramite` como reemplazo del Fondo Interviniente o del procedimiento de
contratación.

## 13. Decisiones pendientes antes de implementar

Requieren definición funcional o arquitectónica previa:

1. representación definitiva del Fondo Interviniente;
2. estados y transiciones de la Solicitud de Intervención;
3. estructura y ciclo de vida de la Evaluación Administrativa;
4. condiciones para registrar y modificar una Decisión Administrativa;
5. mecanismo de identificación y numeración de solicitudes;
6. cardinalidad de evaluaciones y decisiones por solicitud;
7. tratamiento de rectificaciones o reemplazos de decisiones;
8. creación manual o automática del expediente;
9. estrategia de vinculación de expedientes preexistentes;
10. permisos asociados a operadores y autoridades decisoras.

Estas cuestiones no deberán resolverse mediante supuestos técnicos.

## 14. Restricciones de implementación

- No crear un expediente antes de la decisión administrativa en el nuevo flujo.
- No exigir Fondo Interviniente al registrar la solicitud.
- No representar Fondo Interviniente como sinónimo de procedimiento de
  contratación.
- No eliminar la compatibilidad con expedientes existentes durante la
  transición.
- No perder la trazabilidad entre entidades.
- No incorporar reglas de negocio que no estén documentadas y aprobadas.

## 15. Condición previa a la migración

Antes de modificar backend, frontend o persistencia deberá existir un plan de
migración aprobado que:

- identifique componentes afectados;
- ordene las fases;
- establezca compatibilidad;
- defina pruebas y rollback;
- preserve los datos y funcionalidades vigentes.
