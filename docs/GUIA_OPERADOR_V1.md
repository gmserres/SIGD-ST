# Guía rápida del operador — SIGD-ST V1

Esta guía resume el circuito moderno de Fondo Compensador. Para reglas,
estados y compatibilidad histórica consulte
[GUIA_FUNCIONAL_V1.md](GUIA_FUNCIONAL_V1.md).

## Antes de comenzar

- Trabaje siempre dentro de la Solicitud y del Expediente correctos.
- Cada Expediente es una rama independiente.
- Cada OP posee control, Disposición y formalización propios.
- Use la “Próxima acción” como orientación; no reemplaza el criterio
  administrativo.

## 1. Registrar la Solicitud

Complete procedencia, fecha, establecimiento, solicitante, motivo y prioridad.
Si proviene de SUNA, informe su ID. Verifique que aparezca como `REGISTRADA`.

**Bloqueos frecuentes:** fecha inválida, número duplicado o ID SUNA ausente
cuando es obligatorio.

## 2. Registrar la Decisión

Informe autoridad, fecha, resultado, fundamento, fondo y usuario. Para el flujo
de Fondo Compensador debe existir una Decisión aprobatoria con fondo
`FONDO_COMPENSADOR`.

## 3. Crear o abrir un Expediente

Una Solicitud puede tener varios Expedientes. Complete número interno, número
GDEBA si existe, establecimiento y objeto. Al crearlo, la interfaz abre su
detalle. No confunda esta rama con otros Expedientes de la misma Solicitud.

## 4. Completar preparación y documentación

Revise datos administrativos e incorpore los documentos digitales disponibles.
Complete el checklist físico para dejar constancia de la documentación
controlada. El checklist no reemplaza los archivos ni consulta ARCA/ARBA.

## 5. Seleccionar proveedor

Elija un proveedor activo del Maestro. La selección es propia del Expediente.
Si debe reemplazarlo, elija otro proveedor e informe un motivo; el historial
anterior se conserva.

**Bloqueos frecuentes:** Maestro vacío, proveedor inactivo, mismo proveedor o
reemplazo sin motivo.

## 6. Validar el Expediente

Revise errores y advertencias. Registre validación normal o con observaciones;
esta última exige motivo. Si una actuación posterior invalida la validación,
el estado será `PENDIENTE_REVALIDACION` y deberá revalidar.

## 7. Incorporar cada OP

Cargue la OP dentro del Expediente. Identifique su `documento_op_id`. Si hay
varias, trate cada bloque por separado.

## 8. Controlar Proveedor ↔ OP

Ejecute **Controlar proveedor** para crear evidencia administrativa. Un GET o
refresco sólo reconstruye la comparación; no sustituye el POST explícito.

- `COINCIDE`: continúe con la habilitación.
- `CUIT_DIFERENTE`: regularice y ejecute otro control.
- `NO_VERIFICABLE`: revise/reemplace la documentación y reintente.

## 9. Regularizar si corresponde

No cambie el proveedor silenciosamente. Confirme su existencia/estado en el
Maestro, reemplace la selección del Expediente con motivo y ejecute un nuevo
control para esa OP. Verifique que otras ramas y OP no hayan cambiado.

## 10. Verificar habilitación

F5 debe mostrar `HABILITADO` para la OP concreta. Si pide selección, control,
reasignación o revisión documental, complete esa actuación antes de avanzar.
La emisión también exige Expediente `VALIDADO` y validación vigente.

## 11. Preparar y emitir la Disposición

Genere el borrador dentro del bloque de la OP, revise texto y snapshots e
informe manualmente un número único. Emita una sola vez. Compruebe que el DOCX
definitivo quede accesible.

**Bloqueos frecuentes:** borrador obsoleto, número vacío/duplicado, control o
selección modificados, OP no apta o Disposición ya existente.

## 12. Registrar formalización

Formalice cada Disposición por separado. La fecha no puede ser futura ni
anterior a la emisión. Emisión y formalización no son lo mismo.

## 13. Repetir por cada OP

Antes de cerrar, cada OP debe tener su propia Disposición formalizada. La
acción de una OP no completa las demás.

## 14. Cerrar o desistir

**Cerrar:** el Expediente debe estar `VALIDADO`, tener al menos una OP y todas
sus Disposiciones formalizadas. Confirme completitud e informe una fecha no
anterior a la última formalización.

**Desistir:** sólo es posible si no existe ninguna OP. Informe fecha y motivo.
No afecta otros Expedientes ni finaliza automáticamente la Solicitud.

## 15. Archivar

Archive explícitamente un Expediente `CERRADO` o `DESISTIDO`. La fecha no puede
ser anterior a su finalización. Archivar no elimina ni mueve documentos.

## 16. Consultar timeline

Use el timeline del Expediente para su rama y el de la Solicitud para la vista
agregada. Los eventos se reconstruyen desde PostgreSQL y sobreviven a
reinicios. Cuando sólo existe fecha, la precisión es diaria.

## Casos históricos

Los Expedientes marcados como circuito histórico/legacy se consultan por su
flujo compatible: `DISPOSICION_EMITIDA` permite registrar firma, `FIRMADO`
permite archivo y `ARCHIVADO` queda en consulta. No use ese circuito para casos
nuevos.
