# Sprint 0016 - IA Documental Base

## Objetivo

Iniciar la transición desde análisis simulado hacia análisis documental real.

## Implementado

- Lectura de texto desde PDF.
- Extracción inicial por patrones.
- Integración con `analizar-op`.
- Modo híbrido:
  - si hay texto, usa `ALFA_PDF_TEXTO`;
  - si no hay texto, advierte que puede ser PDF escaneado;
  - si no existe OP, mantiene el bloqueo correspondiente.

## Campos extraídos

- CUIT.
- Fecha.
- Número de OP.
- Importe probable.
- Proveedor probable.
- UC.
- Procedimiento.
- Encuadre legal.

## Limitaciones

- No hace OCR todavía.
- Si el PDF es imagen escaneada, no podrá leerlo.
- La identificación de proveedor e importes es inicial y se irá ajustando con documentos reales.

## Próximo sprint

Sprint 0017-0020:

- Comparador OP vs Factura.
- Estado inteligente del expediente.
- Bandeja dinámica con alertas.
