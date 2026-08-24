# SIGD-ST

Sistema Inteligente de Gestión Documental para la Secretaría Técnica del
Consejo Escolar de General Alvarado.

## Estado actual

SIGD-ST V1 es una versión demostrable del circuito de Fondo Compensador. El
sistema organiza Solicitudes de Intervención, Decisiones, Expedientes,
proveedores, documentación y Órdenes de Pago; controla la habilitación del
proveedor, emite y formaliza Disposiciones y registra el cierre, desistimiento
y archivo del Expediente.

La arquitectura local utiliza:

- backend FastAPI sobre Python 3.12;
- PostgreSQL con migraciones Alembic;
- frontend React/Vite;
- filesystem local para uploads y DOCX generados.

## Instalación local

La guía oficial para preparar una instancia desde un clon limpio es
[`docs/INSTALACION_LOCAL.md`](docs/INSTALACION_LOCAL.md).

Documentación funcional de referencia:

- [`docs/GUIA_FUNCIONAL_V1.md`](docs/GUIA_FUNCIONAL_V1.md): modelo, reglas,
  circuitos modernos, compatibilidad legacy y límites de la V1;
- [`docs/GUIA_OPERADOR_V1.md`](docs/GUIA_OPERADOR_V1.md): recorrido breve para
  la operación cotidiana.

Requisitos básicos:

- Python 3.12;
- Node.js `^20.19.0` o `>=22.12.0` y npm;
- PostgreSQL disponible, con una base y un usuario creados previamente.

Después de completar la configuración, migraciones y bootstrap indicados en la
guía, puede iniciarse el entorno local con:

```bat
scripts\iniciar_sigd_st.bat
```

Servicios locales:

- frontend: `http://localhost:5173`;
- API: `http://localhost:8000`;
- documentación API: `http://localhost:8000/docs`.

Los scripts `.bat` requieren Windows y que Python, Node.js y npm estén
disponibles en `PATH`. El procedimiento de referencia no es Docker Compose: el
archivo actual es experimental y todavía no reproduce la instalación completa.

## Alcance operativo

La V1 permite una demostración integral en un entorno local controlado. No está
preparada para producción institucional sin resolver, entre otros aspectos:

- autenticación y autorización;
- política y automatización de backup/restauración;
- protección operativa del almacenamiento documental;
- configuración para acceso desde otros hosts;
- procedimiento institucional para renovar la Configuración UC anual.

Los datos de desarrollo y el escenario F6CFINAL no forman parte del bootstrap
de una instalación nueva.
