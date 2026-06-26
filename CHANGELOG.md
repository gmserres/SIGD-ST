# CHANGELOG

## Commit 0006

- Se agrega endpoint de estado del sistema.
- Se agrega motor de validaciones mínimas del expediente.
- Se agrega endpoint `GET /expedientes/{id}/validacion`.
- Se incorpora panel de validación en la ficha del expediente.
- Se mejora la interfaz para mostrar errores, advertencias y controles.
- Se documenta instalación local.
- Se documenta prueba manual del flujo Alfa.
- Se estabiliza la base para el próximo commit de generación documental.

## Commit 0005

- Se implementa el primer Motor IA de Orden de Pago en modo Alfa.
- Se agrega endpoint `POST /expedientes/{id}/analizar-op`.
- Se agrega estructura de respuesta para análisis de OP.
- Se agrega cálculo automático de UC.
- Se agrega determinación inicial del procedimiento.
- Se agregan reglas iniciales de Fondo Compensador.
- Se registra historial al analizar OP.
- Se incorpora vista de Análisis IA en la ficha del expediente.

## Commit 0004

- Se implementa carga física de documentos al expediente.
- Se crea servicio de almacenamiento en `storage/expedientes`.
- Se permite subir OP desde la interfaz.
- Se permite subir documentos generales desde la Ficha del Expediente.
- Se registra cada documento en el expediente.
- Se registra historial automático al cargar documentos.
- Se agregan endpoints de descarga y visualización de documentos.

## Commit 0003

- Se reemplaza el frontend inicial por una interfaz de trabajo orientada al expediente.
- Se agrega Panel Principal.
- Se agrega navegación lateral.
- Se agrega pantalla Nuevo Expediente.
- Se agrega pantalla Mis Expedientes.
- Se agrega Ficha del Expediente.

## Commit 0002

- Se agrega Documento asociado al expediente.
- Se agrega Historial del Expediente.
- Se agregan Proveedores.
- Se agregan Establecimientos.
- Se agrega API de Catálogos.

## Commit 0001

- Se crea estructura inicial del repositorio SIGD-ST.
- Se implementa API base de expedientes.
