# CHANGELOG

## Sprint 0017

- Se mejora la extracción de importes por contexto.
- Se evita que el CBU sea interpretado como importe.
- Se incorporan reglas de exclusión para CBU, CUIT, liquidación y códigos largos.
- Se priorizan etiquetas documentales: `Monto Total de Facturas`, `Monto Neto a Pagar`, `Importe`, `Total`.
- Se agrega confianza porcentual al importe detectado dentro de las validaciones de IA.
- Se actualiza el modo de análisis a `ALFA_PDF_TEXTO_V2`.

## Sprint 0016

- Se incorpora extracción inicial de texto real desde PDF.
- Se detectan CUIT, fecha, número de OP, proveedor probable e importe probable.
- Se calcula UC desde el importe detectado.
