# SIGD-ST V1 — Guía funcional y operativa

Este documento describe el comportamiento funcional vigente de SIGD-ST V1.
El código, los contratos API, la persistencia PostgreSQL y los tests son sus
fuentes autoritativas. Los documentos de sprints y modelos anteriores se
conservan como antecedentes históricos.

## 1. Propósito y alcance

SIGD-ST administra intervenciones de la Secretaría Técnica con trazabilidad
desde la necesidad inicial hasta su finalización documental. La V1 implementa
el circuito operativo de **Fondo Compensador**: registra Solicitudes y
Decisiones, organiza Expedientes, controla documentación y proveedores,
procesa Órdenes de Pago (OP), emite y formaliza Disposiciones y permite cerrar,
desistir y archivar cada rama administrativa.

La **Solicitud de Intervención es la raíz conceptual**. El Expediente no la
reemplaza: representa una rama administrativa originada en ella.

```text
Solicitud de Intervención
└── 0..N Expedientes independientes
    ├── proveedor vigente del Expediente
    ├── documentos y validación
    └── 0..N Órdenes de Pago
        ├── control Proveedor ↔ OP
        ├── habilitación del proveedor
        ├── 0..1 Disposición definitiva
        └── formalización individual
    └── cierre o desistimiento
        └── archivo institucional
```

## 2. Modelo administrativo

### 2.1 Solicitud de Intervención

La Solicitud registra la necesidad inicial. Conserva número, procedencia,
fecha de ingreso, establecimiento, solicitante, motivo, prioridad, estado y,
cuando corresponde, ID SUNA. Si la procedencia es `SUNA`, el ID SUNA es
obligatorio.

Puede existir sin Decisión y puede originar cero, uno o varios Expedientes. Es
un nivel agregador: cerrar, desistir o archivar un Expediente no finaliza
automáticamente la Solicitud ni afecta a sus otras ramas.

### 2.2 Decisión administrativa

La Decisión pertenece a la Solicitud y registra:

- resultado;
- autoridad decisora;
- fecha;
- fundamento;
- fondo interviniente, cuando corresponde;
- descripción del fondo para el caso `OTRO`;
- usuario registrante.

El flujo permite registrar la actuación de la autoridad competente. No existe
en V1 una entidad durable separada de “Evaluación Administrativa”. La
autenticación y los permisos formales por rol tampoco están implementados: los
catálogos y campos de usuario no constituyen un sistema de autorización.

### 2.3 Solicitud 1:N Expedientes

Cada Expediente conserva su propia identidad, estado, proveedor, documentos,
checklist, validaciones, OP, controles, Disposiciones, formalizaciones,
finalización, timeline y próxima acción. Una operación sobre el Expediente A
no debe modificar ni inferir estado en el Expediente B, aunque ambos provengan
de la misma Solicitud.

El timeline de la Solicitud agrega los acontecimientos propios de la Solicitud
y los de sus Expedientes sin perder `expediente_id` ni `documento_op_id`.

## 3. Expediente

El Expediente conserva, entre otros datos:

- número interno;
- número GDEBA opcional;
- Solicitud y Decisión de origen;
- configuración UC aplicada;
- tipo de trámite y estado;
- establecimiento y objeto;
- fechas y metadatos de finalización.

El número interno y el número GDEBA son referencias administrativas distintas.
SIGD-ST no crea ni sincroniza automáticamente un Expediente GDEBA.

Estados vigentes del modelo: `BORRADOR`, `DOCUMENTACION_EN_CARGA`,
`PENDIENTE_VALIDACION`, `PENDIENTE_REVALIDACION`, `VALIDADO`, los estados
históricos `DISPOSICION_EMITIDA` y `FIRMADO`, y los terminales `CERRADO`,
`DESISTIDO` y `ARCHIVADO`.

## 4. Proveedores

### 4.1 Maestro

El Maestro registra CUIT normalizado, razón social y condición activo/inactivo.
Permite alta, consulta, modificación de razón social y cambio de estado. No
elimina la historia de selecciones anteriores.

### 4.2 Selección por Expediente

La selección representa la asignación administrativa previa para un
Expediente concreto. Guarda snapshots del CUIT y razón social, la Decisión y
Solicitud de origen, quién seleccionó y cuándo. Sólo puede existir una
selección vigente por Expediente.

El reemplazo es explícito, exige un proveedor activo distinto y un motivo.
Finaliza la vigencia anterior y crea una nueva selección con fecha estrictamente
posterior; el historial conserva ambas.

### 4.3 OP como fuente documental

La OP controla documentalmente al proveedor destinado al pago. El CUIT es la
identidad primaria; la razón social es complementaria. Si el CUIT documental
difiere del seleccionado, SIGD-ST no sobrescribe ni reasigna silenciosamente:
el operador debe regularizar el Maestro si corresponde, reemplazar la selección
con motivo y ejecutar un nuevo control.

Los snapshots históricos no se reconstruyen desde el estado actual del Maestro.

## 5. Documentos, checklist y validación

### 5.1 Documentación digital

Los metadatos se persisten en PostgreSQL y los archivos se almacenan en el
filesystem. Cada documento pertenece a un Expediente. La OP se carga y se
direcciona mediante su `documento_op_id`; no existe una OP global implícita.

### 5.2 Checklist físico

El checklist persistido registra la existencia o control administrativo de
factura, remito/conformidad, CAE, ARCA, ARBA y documentación adicional según el
contrato vigente. No implica digitalización integral del expediente físico ni
consultas automáticas a ARCA o ARBA.

### 5.3 Validación administrativa

La evaluación de controles puede producir errores y advertencias. El operador
puede registrar:

- `VALIDADA`;
- `VALIDADA_CON_OBSERVACIONES`, con motivo obligatorio.

La validación vigente es la fuente autoritativa. Una actuación posterior que
invalida la validación lleva al Expediente a `PENDIENTE_REVALIDACION`; debe
registrarse una nueva validación antes de continuar. Timeline e
`HistorialService` no habilitan funciones.

## 6. Orden de Pago

Cada OP es una unidad documental independiente del Expediente y posee su propio:

- `documento_op_id`;
- análisis dirigido;
- control de proveedor;
- habilitación F5;
- Disposición;
- formalización.

Varias OP del mismo Expediente no comparten automáticamente control,
Disposición ni formalización. Las operaciones modernas siempre se dirigen por
`expediente_id + documento_op_id`.

El análisis de una OP reconstruye datos documentales como proveedor, CUIT,
importe, número de OP, liquidación y datos para determinar el procedimiento.
Una extracción fallida o insuficiente bloquea las operaciones que requieren
esos datos.

## 7. Control Proveedor ↔ OP

El comparador puro normaliza CUIT y produce únicamente:

| Resultado | Significado | Consecuencia |
|---|---|---|
| `COINCIDE` | El CUIT de la selección vigente equivale al detectado en la OP. | Puede habilitar F5 si el control es el último y corresponde a esa selección. |
| `CUIT_DIFERENTE` | Los CUIT válidos son distintos. | Exige regularización/reasignación explícita y un nuevo control. |
| `NO_VERIFICABLE` | La OP no permite determinar un CUIT confiable. | Exige revisar o reemplazar documentación y reintentar. |

La diferencia o ausencia de razón social no cambia `COINCIDE` cuando el CUIT
coincide; queda como advertencia nominal. Cada POST persistible crea una nueva
evidencia append-only. El GET reconstruye la comparación, pero no crea
evidencia administrativa.

## 8. Habilitación F5

F5 es un read model derivado para una OP concreta. No se persiste. Sus estados
son:

- `HABILITADO`;
- `REQUIERE_REASIGNACION_PROVEEDOR`;
- `REQUIERE_SELECCION_PROVEEDOR`;
- `REQUIERE_NUEVO_CONTROL`;
- `PROVEEDOR_NO_VERIFICABLE`;
- `SIN_SOLICITUD_ASOCIADA`.

`HABILITADO` requiere Solicitud asociada, selección vigente del Expediente y
el último control autoritativo de esa OP correspondiente exactamente a esa
selección, con estado `COINCIDE` y CUIT documental. La identidad interna del
proveedor proviene de la selección; CUIT y razón social definitiva son
snapshots de la OP. La razón social documental puede ser nula.

F5 no sustituye la validación administrativa del Expediente. Para emitir la
Disposición, además de F5, se comprueban estado `VALIDADO`, validación vigente,
OP apta, configuración UC y datos administrativos suficientes.

## 9. Disposición por OP

El circuito moderno permite una Disposición definitiva por OP y varias
Disposiciones en un mismo Expediente. El número de Disposición es manual y
único. La emisión conserva:

- identidad de Expediente y OP;
- configuración y valor UC aplicados;
- número de OP y liquidación;
- importe y cantidad UC;
- procedimiento y normativa;
- proveedor, CUIT y snapshots habilitantes;
- selección y control utilizados;
- texto emitido y ruta del DOCX;
- fecha de emisión.

El borrador se genera por OP y puede editarse antes de emitir. Si cambia la
selección o el control habilitante, el contexto anterior queda obsoleto. La
persistencia vuelve a validar el contexto para evitar emitir con evidencia
vencida. Una segunda emisión para la misma OP es rechazada.

La emisión genera un DOCX definitivo y **no cambia** el estado moderno del
Expediente: éste permanece `VALIDADO`. `Expediente.numero_disposicion` no es la
fuente del circuito moderno; se conserva para compatibilidad histórica.

## 10. Configuración UC y procedimiento

La carga inicial versionada vigente contiene:

- inicio de vigencia: 13/03/2025;
- valor UC: ARS 1.677;
- resolución: OPC 54/2025;
- organismo: Organismo Provincial de Contrataciones.

| Cantidad UC | Procedimiento | Artículo/inciso | Referencia |
|---|---|---|---|
| 0 a 10.000 inclusive | Factura Conformada | 18 inc. C | Ley 13.981 |
| Más de 10.000 a 50.000 inclusive | Procedimiento Abreviado | 18 inc. B | Ley 13.981 |
| Más de 50.000 a 100.000 inclusive | Contratación menor por monto | 18 inc. A | Ley 13.981 |

La configuración se versiona, posee vigencia y se carga mediante bootstrap
idempotente. V1 no automatiza la aprobación ni renovación institucional anual:
los valores futuros deben confirmarse y registrarse administrativamente.

## 11. Formalización

Emisión y formalización son actuaciones distintas. La formalización se registra
individualmente sobre una Disposición emitida y conserva fecha de
formalización, usuario (`sistema` en el flujo actual) y fecha-hora de registro.
No puede ser anterior a la emisión ni repetirse. Varias Disposiciones se
formalizan independientemente y el Expediente permanece `VALIDADO`.

## 12. Cierre, desistimiento y archivo

### 12.1 Cierre ordinario

El cierre sólo se habilita cuando:

- el Expediente está `VALIDADO`;
- posee al menos una OP;
- cada OP posee su Disposición definitiva;
- todas esas Disposiciones están formalizadas.

La fecha de cierre no puede ser futura ni anterior a la última formalización y
se exige confirmación explícita de completitud. El sistema registra usuario
`sistema`, fecha y fecha-hora, y pasa el Expediente a `CERRADO`.

### 12.2 Desistimiento

Puede registrarse en `BORRADOR`, `DOCUMENTACION_EN_CARGA`,
`PENDIENTE_VALIDACION`, `PENDIENTE_REVALIDACION` o `VALIDADO`, siempre que el
Expediente no posea ninguna OP. Exige fecha no futura ni anterior a la creación
y motivo obligatorio. Conserva las actuaciones anteriores y pasa a
`DESISTIDO`. No desiste automáticamente la Solicitud ni sus otros Expedientes.

### 12.3 Archivo institucional

El archivo moderno es una acción explícita sobre un Expediente `CERRADO` o
`DESISTIDO`. La fecha no puede ser anterior a la finalización. Registra usuario
`sistema`, conserva la procedencia original (cierre o desistimiento) y pasa a
`ARCHIVADO`.

Archivar no borra ni mueve físicamente documentos, OP, controles,
Disposiciones, snapshots o DOCX. `CERRADO`, `DESISTIDO` y `ARCHIVADO` forman la
barrera terminal que impide nuevas actuaciones administrativas ordinarias.

## 13. Timeline durable

No existe una tabla paralela de eventos. El timeline se reconstruye desde las
fuentes PostgreSQL autoritativas: Solicitud, Decisiones, Expedientes,
documentos, checklist, validaciones, selecciones, controles, Disposiciones y
metadatos de finalización.

El timeline del Expediente mantiene identidad de OP y orden determinista. El
timeline de la Solicitud agrega `SOLICITUD_INGRESADA`,
`DECISION_ADMINISTRATIVA` y los timelines de todas sus ramas conservando
`expediente_id`. Sobrevive a reinicios y no depende de `HistorialService`.

Cuando una fuente sólo almacena fecha, el timeline declara precisión `DIA`; no
inventa una hora administrativa.

## 14. Próxima acción

La próxima acción es un read model derivado bajo demanda. No se persiste, no
crea una máquina de estados paralela y evalúa todas las OP. Orienta Mesa de
Control, listados y detalle.

La prioridad real sigue, en términos operativos, esta matriz:

| Situación | Próxima acción |
|---|---|
| Preparación incompleta | Completar preparación |
| Sin validación vigente | Completar validación |
| `PENDIENTE_REVALIDACION` | Revalidar expediente |
| Validado sin OP | Incorporar Orden de Pago |
| OP sin selección | Seleccionar proveedor |
| Selección sin control vigente | Controlar proveedor |
| CUIT diferente | Regularizar proveedor |
| Proveedor no verificable | Revisar documentación de la OP |
| OP habilitada sin Disposición | Preparar Disposición |
| Disposición sin formalizar | Registrar formalización |
| Todas las OP formalizadas | Cerrar expediente |
| `CERRADO` o `DESISTIDO` | Archivar expediente |
| `ARCHIVADO` | Consulta histórica |

Con varias OP se elige la candidata de mayor prioridad y se conserva su
`documento_op_id` para navegar al bloque correcto.

## 15. Compatibilidad con Expedientes históricos

El circuito global de Disposición por Expediente está congelado para nuevas
escrituras. Los endpoints de borrador/emisión global permanecen deprecated o
bloqueados, mientras la lectura histórica continúa disponible.

Una Disposición legacy puede no poseer OP asociada. Los Expedientes legacy en
`DISPOSICION_EMITIDA` pueden registrar firma; los que están `FIRMADO` pueden
usar el archivo histórico. Un `ARCHIVADO` legacy sin causa moderna se conserva
como consulta histórica y no se reinterpreta como cierre o desistimiento. El
campo global `numero_disposicion` permanece como snapshot histórico, no como
fuente para casos nuevos.

## 16. Roles y responsabilidades

### Operador

- registra Solicitudes y las actuaciones disponibles en la interfaz;
- crea/abre Expedientes desde una Decisión aprobatoria;
- completa datos, documentos y checklist;
- selecciona o reemplaza proveedor con motivo;
- ejecuta controles por OP y regulariza discrepancias;
- prepara y emite cada Disposición con número manual;
- registra fechas de formalización, cierre/desistimiento y archivo.

### Autoridad administrativa

- adopta la Decisión sobre la intervención;
- determina resultado, fundamento y fondo interviniente;
- aporta el criterio administrativo para selección, regularización,
  validación y finalización.

SIGD-ST registra esos datos, pero V1 no autentica ni autoriza formalmente a la
persona que actúa.

### Sistema

- asigna identidades técnicas y normaliza CUIT;
- aplica barreras y restricciones de concurrencia;
- deriva controles, habilitaciones y próxima acción;
- reconstruye timelines desde PostgreSQL;
- genera y conserva snapshots y DOCX;
- registra `sistema` en formalización/finalización/archivo donde el flujo
  actual así lo establece.

## 17. Qué no hace V1

V1 no incluye todavía:

- autenticación, autorización productiva ni permisos institucionales por rol;
- despliegue productivo o multiusuario endurecido;
- CORS y acceso LAN/Internet productivos;
- Docker Compose productivo;
- backup automatizado, retención o restauración ensayada institucionalmente;
- protección/replicación institucional del filesystem documental;
- integración automática con GDEBA;
- integración automática con SUNA, ARCA o ARBA;
- digitalización integral del expediente físico;
- renovación anual automática de Configuración UC;
- una Evaluación Administrativa durable separada de la Decisión;
- cierre automático de la Solicitud por finalizar uno de sus Expedientes;
- eliminación administrativa integral de cadenas de prueba;
- F6D2B, que permanece pausado.

La extracción de OP depende del documento disponible y puede resultar
`NO_VERIFICABLE`; no constituye una integración con el organismo emisor.

## 18. Referencias operativas

- Instalación: [INSTALACION_LOCAL.md](INSTALACION_LOCAL.md)
- Uso cotidiano: [GUIA_OPERADOR_V1.md](GUIA_OPERADOR_V1.md)
- Contratos HTTP: `/docs` de la instancia backend
- Variables de plantillas: [CATALOGO_VARIABLES_PLANTILLAS.md](CATALOGO_VARIABLES_PLANTILLAS.md)
