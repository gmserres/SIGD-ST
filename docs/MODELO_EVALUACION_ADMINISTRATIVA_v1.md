# Modelo funcional de Evaluación Administrativa v1

## 1. Propósito

La Evaluación Administrativa representa la etapa de análisis previa a la
Decisión Administrativa sobre una Solicitud de Intervención.

Su propósito es conservar de forma trazable los antecedentes, consultas,
análisis y verificaciones necesarios para que la autoridad competente pueda
adoptar posteriormente una decisión fundada.

La Evaluación Administrativa no constituye por sí misma una decisión ni
determina automáticamente el resultado de la intervención.

## 2. Diferencia entre Evaluación Administrativa y Decisión Administrativa

La Evaluación Administrativa reúne, analiza y documenta información relacionada
con la Solicitud de Intervención.

La Decisión Administrativa representa la determinación adoptada por la
autoridad competente después de considerar la solicitud y las evaluaciones
correspondientes.

Por lo tanto:

- la evaluación aporta antecedentes y elementos de análisis;
- la decisión expresa la determinación de la autoridad competente;
- una evaluación no debe utilizarse como reemplazo de una decisión;
- el evaluador no debe ser interpretado automáticamente como autoridad
  decisora;
- la finalización de una evaluación no implica por sí misma que exista una
  Decisión Administrativa.

## 3. Relación con la Solicitud de Intervención

Toda Evaluación Administrativa deberá vincularse explícitamente con una
Solicitud de Intervención.

La relación deberá permitir:

- identificar la solicitud evaluada;
- consultar las evaluaciones asociadas;
- reconstruir la secuencia de análisis realizada;
- conservar los responsables y observaciones registrados;
- mantener la trazabilidad hasta la Decisión Administrativa posterior, cuando
  esta exista.

No deberá existir una Evaluación Administrativa desvinculada de una Solicitud
de Intervención.

## 4. Datos mínimos candidatos

Se identifican como datos mínimos candidatos:

- `id_evaluacion`
- `solicitud_intervencion_id`
- `fecha_inicio`
- `evaluador`
- `estado`
- `observaciones`

Estos datos son candidatos para orientar la definición posterior. Su inclusión
en este documento no establece todavía:

- tipos técnicos definitivos;
- obligatoriedad definitiva de cada dato;
- formatos;
- catálogos;
- estados permitidos;
- reglas de modificación;
- reglas de finalización.

`id_evaluacion` deberá distinguirse de cualquier numeración o referencia
administrativa que pudiera definirse posteriormente.

`solicitud_intervencion_id` representa la referencia necesaria para mantener
la trazabilidad con la Solicitud de Intervención.

## 5. Cardinalidad candidata

Como criterio funcional candidato:

```text
Solicitud de Intervención 1 → 0..N Evaluaciones Administrativas
```

Esto permite contemplar que:

- una solicitud pueda no tener todavía evaluaciones;
- una solicitud pueda requerir más de una evaluación;
- las evaluaciones conserven identidad y trazabilidad propias.

Permanece expresamente pendiente confirmar si una Solicitud de Intervención
puede tener más de una Evaluación Administrativa activa al mismo tiempo.

La cardinalidad candidata no deberá utilizarse para inferir reglas de
concurrencia, orden, reemplazo o cierre.

## 6. Reglas funcionales aprobadas

La Evaluación Administrativa:

1. se vincula con una Solicitud de Intervención;
2. conserva antecedentes, consultas, análisis y verificaciones;
3. no determina por sí misma el Fondo Interviniente;
4. no crea automáticamente un Expediente;
5. no reemplaza la Decisión Administrativa;
6. debe mantener trazabilidad con la solicitud;
7. debe permitir identificar los responsables y elementos de análisis
   efectivamente registrados.

La existencia de una evaluación no implica que la solicitud deba producir
necesariamente una Decisión Administrativa o un Expediente.

## 7. Posibles responsabilidades

Sin establecer todavía reglas definitivas, la Evaluación Administrativa podría
comprender responsabilidades como:

- registrar antecedentes relevantes;
- documentar consultas administrativas;
- incorporar análisis técnicos;
- registrar verificaciones realizadas;
- conservar observaciones;
- identificar a quien realiza la evaluación;
- aportar elementos para una futura Decisión Administrativa;
- mantener la trazabilidad de las actuaciones registradas.

Estas responsabilidades no autorizan al componente de evaluación a:

- seleccionar automáticamente el Fondo Interviniente;
- definir el procedimiento de contratación;
- adoptar una Decisión Administrativa;
- crear un Expediente;
- emitir una Disposición.

## 8. Riesgos conceptuales

### 8.1 Mezcla con la Decisión Administrativa

Existe riesgo de que una conclusión, recomendación u observación de la
evaluación sea interpretada como decisión de autoridad.

La evaluación debe conservarse como antecedente de análisis y no como
sustitución de la Decisión Administrativa.

### 8.2 Mezcla con la validación documental

La validación documental controla documentación y condiciones del trámite.
La Evaluación Administrativa tiene un alcance previo y más amplio, relacionado
con el análisis de la Solicitud de Intervención.

Un resultado de validación documental no debe representar automáticamente una
Evaluación Administrativa completa, y una evaluación no debe reemplazar los
controles documentales existentes.

### 8.3 Mezcla con el Expediente

La evaluación pertenece al flujo iniciado por la Solicitud de Intervención y
existe antes de la eventual creación o vinculación de un Expediente.

No deberá requerirse un Expediente para registrar una evaluación ni utilizarse
`expediente_id` como sustituto de `solicitud_intervencion_id`.

## 9. Decisiones funcionales pendientes

Antes de implementar el ciclo de vida de la Evaluación Administrativa deberá
definirse:

1. quién puede iniciar una evaluación;
2. quién puede modificarla;
3. quién puede finalizarla;
4. cuáles son sus estados definitivos;
5. qué transiciones se permiten;
6. cuál será la estructura de sus actuaciones;
7. qué datos serán obligatorios;
8. la cardinalidad definitiva por solicitud;
9. si puede existir más de una evaluación activa simultáneamente;
10. si una evaluación puede reabrirse;
11. cómo se rectifica una evaluación;
12. cómo se preservan versiones o antecedentes rectificados;
13. qué relación tendrá con la Decisión Administrativa;
14. si una decisión requiere una o más evaluaciones finalizadas;
15. qué permisos corresponden a cada operación.

Los estados `ABIERTA`, `EN_ANALISIS` y `FINALIZADA` pueden considerarse
alternativas candidatas para discusión. No están aprobados y no deberán
implementarse como valores definitivos.

## 10. Criterio de no implementación

Ninguna decisión funcional pendiente deberá resolverse implícitamente en el
primer código.

En particular, una implementación inicial no deberá:

- crear estados no aprobados;
- asumir una única evaluación por solicitud;
- asumir una única evaluación activa;
- definir automatismos de inicio, cierre o reapertura;
- atribuir permisos a roles existentes sin aprobación;
- convertir observaciones en decisiones;
- determinar el Fondo Interviniente;
- crear o vincular automáticamente un Expediente;
- inventar actuaciones, responsables o transiciones.

La implementación deberá comenzar únicamente después de aprobar el alcance
funcional correspondiente y deberá mantener separadas la Evaluación
Administrativa, la Decisión Administrativa, la validación documental y el
Expediente.
