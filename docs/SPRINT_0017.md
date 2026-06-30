# Sprint 0017 - IA Documental v2

## Objetivo

Robustecer la extracción de importes en Órdenes de Pago reales.

## Problema corregido

El Sprint 0016 tomaba el número más grande del documento como importe probable. En una OP real, el CBU era más grande que el importe y fue tomado erróneamente como monto de contratación.

## Solución

El extractor ahora trabaja por contexto:

1. Busca etiquetas documentales prioritarias.
2. Extrae solo importes monetarios asociados a esas etiquetas.
3. Ignora líneas relacionadas con CBU, CUIT, expedientes o códigos.
4. Descarta valores superiores a un máximo razonable.
5. Informa el contexto usado y confianza.

## Caso de prueba

OP de referencia:

- Proveedor: GROS NICOLAS EZEQUIEL.
- CUIT: 20-36858604-9.
- OP: OP 1/2026.
- Importe correcto: $884.000,00.
- CBU: 0140366203617650870232.

Resultado esperado:

- Importe detectado: 884000.00.
- El CBU debe ser ignorado.
