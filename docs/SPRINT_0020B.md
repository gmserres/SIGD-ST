# Sprint 0020B - Motor de Inteligencia Administrativa

## Objetivo

Pasar de una IA que resume el expediente a un motor que controla la consistencia administrativa.

## Implementado

- Comparador OP vs facturas.
- Confiabilidad documental.
- Prioridad de revisión.
- Controles inteligentes.
- Mensajes preparados para bloqueo inteligente futuro.

## Criterios actuales

### Confiabilidad

Se calcula con reglas objetivas:

- OP presente.
- Proveedor detectado.
- CUIT detectado.
- Importe bruto detectado.
- Importe neto detectado.
- Facturas detectadas.
- Facturas consistentes.
- Retenciones detectadas.
- Menor cantidad de faltantes.

### Prioridad

- Alta: datos esenciales ausentes o inconsistencia económica.
- Media: datos económicos consistentes, pero faltan documentos.
- Baja: expediente completo o casi completo.

## Próximo sprint

Sprint 0021:

- Bloqueo inteligente de validación.
- Bandeja con prioridades.
- Historial IA persistente.
