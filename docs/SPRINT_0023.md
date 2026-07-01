# Sprint 0023 - Validación con Observaciones

## Objetivo

Hacer que la validación refleje el procedimiento administrativo real.

## Estados

### Verde

Apto para validar.

### Amarillo

Puede validar con observaciones. Requiere motivo obligatorio y deja registro en historial.

### Rojo

Bloqueado por errores críticos.

## Reglas

Bloquean:
- Falta OP.
- Falta expediente interno.
- Falta establecimiento.
- Falta objeto.
- Errores críticos de estructura.

No bloquean, pero requieren observación:
- CAE pendiente.
- ARCA pendiente.
- ARBA pendiente.
- Remito/conformidad pendiente.
- Facturas acreditables por checklist.

## Próximo paso

Sprint 0024: generación asistida de disposición.
