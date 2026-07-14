# Modelo de Dominio SIGD-ST v2

## 1. Propósito del sistema

SIGD-ST administra intervenciones administrativas de la Secretaría Técnica, no solamente expedientes ni documentos.

El sistema acompaña el ciclo completo de una intervención desde su ingreso hasta su resolución y archivo, conservando la trazabilidad de las decisiones administrativas adoptadas.

## 2. Entidad raíz: Solicitud de Intervención

Toda intervención administrativa se inicia mediante una Solicitud de Intervención. Esta constituye la entidad raíz del dominio y existe antes de determinar el Fondo Interviniente o crear un expediente.

### Campos mínimos

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

### Regla de procedencia

Si la procedencia de la solicitud es `SUNA`, el campo `id_suna` es obligatorio. Para otras procedencias, el campo `id_suna` será opcional o no aplicable.

El registro inicial de la solicitud no implica la determinación anticipada de un Fondo Interviniente.

## 3. Evaluación Administrativa

La Evaluación Administrativa es la etapa previa a la decisión. Puede comprender consultas, análisis técnicos, antecedentes, verificaciones y otras actividades administrativas necesarias para determinar el Fondo Interviniente.

## 4. Decisión Administrativa

La Decisión Administrativa representa la determinación competente adoptada después del registro y de la Evaluación Administrativa de la Solicitud de Intervención.

El operador registra la Solicitud de Intervención. La determinación del Fondo Interviniente constituye una decisión administrativa reservada a la autoridad competente.

### Campos mínimos

- `solicitud_intervencion_id`
- `fondo_interviniente`
- `autoridad_decisora`
- `fecha_decision`
- `fundamento`
- `observaciones`

La denominación oficial del concepto será siempre **Fondo Interviniente**. No deberá utilizarse la expresión “procedimiento elegido” para representar esta decisión.

## 5. Separación conceptual

SIGD-ST distingue dos conceptos administrativos diferentes.

### Fondo Interviniente

Identifica el fondo o ámbito institucional que interviene en la atención de la solicitud.

Ejemplos:

- Fondo Compensador
- CUFP
- Fondo Educativo
- Otro

### Procedimiento de contratación

Identifica el mecanismo administrativo de contratación aplicable dentro del trámite correspondiente.

Ejemplos:

- Factura Conformada
- Procedimiento Abreviado
- Contratación Menor
- Licitación
- Otros procedimientos previstos por la normativa

La determinación del Fondo Interviniente no equivale a la definición del procedimiento de contratación. Ambos conceptos deben modelarse y registrarse de forma independiente.

## 6. Decisión pendiente de arquitectura

Se encuentra pendiente definir la representación definitiva del Fondo Interviniente.

### Opción A: catálogo institucional

El Fondo Interviniente se representa mediante un catálogo administrado por el sistema.

**Ventajas:**

- implementación simple;
- validación uniforme de valores;
- bajo acoplamiento con el resto del dominio;
- incorporación sencilla de nuevos fondos;
- adecuada para fondos que solo requieren código, nombre y estado.

**Desventajas:**

- capacidad limitada para representar reglas y comportamiento propios;
- dificultad para asociar responsables, normativa, vigencia y configuración compleja;
- posible crecimiento desordenado si se agregan atributos específicos.

### Opción B: entidad propia del dominio

El Fondo Interviniente se representa como una entidad con identidad, atributos, relaciones y ciclo de vida propios.

**Ventajas:**

- permite representar responsables, normativa, vigencia y configuración;
- admite relaciones específicas con decisiones, expedientes y procedimientos;
- facilita la evolución de fondos con comportamiento administrativo propio.

**Desventajas:**

- aumenta la complejidad del modelo;
- requiere servicios, persistencia y reglas adicionales;
- puede resultar excesivo mientras los fondos funcionen como valores institucionales estables.

La decisión entre ambas alternativas permanece abierta y deberá resolverse según las necesidades funcionales verificadas.

## 7. Expediente

El Expediente ya no es la entidad raíz del sistema.

Es una consecuencia de la Decisión Administrativa adoptada sobre una Solicitud de Intervención. Su creación ocurre después de determinar el Fondo Interviniente y debe mantener un vínculo permanente con la solicitud que le dio origen.

Los expedientes existentes podrán continuar siendo administrados durante la transición al nuevo modelo.

## 8. Flujo general

```text
Solicitud de Intervención
          ↓
Evaluación Administrativa
          ↓
Decisión Administrativa
          ↓
 Fondo Interviniente
          ↓
      Expediente
          ↓
      Documentos
          ↓
      Validación
          ↓
     Disposición
          ↓
        Archivo
```

## 9. Diagrama general del dominio

```text
Solicitud de Intervención
          │
          ▼
Evaluación Administrativa
          │
          ▼
Decisión Administrativa
          │
          ▼
 Fondo Interviniente
          │
          ▼
      Expediente
          │
          ├── Documentos
          ├── Validación
          ├── Historial
          └── Disposición
                  │
                  ▼
                Archivo
```

## 10. Trazabilidad

SIGD-ST debe conservar de manera permanente el siguiente vínculo:

```text
Solicitud de Intervención
→ Evaluación Administrativa
→ Decisión Administrativa
→ Fondo Interviniente
→ Expediente
→ Disposición
```

La trazabilidad debe permitir reconstruir el origen, las evaluaciones, las decisiones, los responsables y el resultado de cada intervención administrativa.

## 11. Consultas futuras

El sistema deberá permitir búsquedas y consultas por:

- número de solicitud;
- ID SUNA;
- expediente interno;
- expediente GDEBA;
- disposición.

Las consultas deberán permitir recorrer la relación completa entre la Solicitud de Intervención y los elementos administrativos derivados.

## 12. Decisiones arquitectónicas

### DA-001: La Solicitud de Intervención es la entidad raíz del dominio

Toda intervención administrativa comienza con una Solicitud de Intervención. El Expediente y los documentos posteriores son entidades derivadas de la Evaluación Administrativa y de la Decisión Administrativa.

Esta decisión permite registrar solicitudes antes de conocer el Fondo Interviniente y conservar su trazabilidad desde el ingreso.

### DA-002: Fondo Interviniente y procedimiento de contratación son conceptos distintos

El Fondo Interviniente identifica el ámbito institucional que atenderá la solicitud. El procedimiento de contratación identifica el mecanismo utilizado para instrumentar una contratación.

SIGD-ST deberá representar ambos conceptos por separado y evitar que la selección de uno determine implícitamente el otro.

### DA-003: El dominio se organiza alrededor de la Intervención Administrativa

El dominio del sistema se organiza alrededor de la Intervención Administrativa y no del Expediente.

El Expediente constituye una consecuencia administrativa de una decisión adoptada sobre una Solicitud de Intervención.

La arquitectura futura deberá preservar este principio.
