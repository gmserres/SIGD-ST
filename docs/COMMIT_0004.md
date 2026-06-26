# Commit 0004

## Objetivo

Implementar la gestión documental real del expediente.

## Implementado

- Carga física de archivos.
- Carpeta automática por expediente.
- Registro de documentos asociados.
- Historial automático de carga documental.
- Visualización y descarga de documentos.
- Carga de OP desde la interfaz.
- Carga de documentos complementarios desde la ficha.

## Endpoints agregados / modificados

- POST /expedientes/{id}/documentos/op
- POST /expedientes/{id}/documentos/upload
- GET /expedientes/{id}/documentos
- GET /expedientes/{id}/documentos/{documento_id}/descargar

## Pendiente para Commit 0005

- Motor IA para lectura inicial de Orden de Pago.
- Extracción estructurada de datos desde PDF.
- Vista de análisis IA dentro de la ficha.
