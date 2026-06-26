# SIGD-ST

Sistema Inteligente de Gestión Documental para la Secretaría Técnica del Consejo Escolar de General Alvarado.

## Estado actual

Versión Alfa 0.6.0.

El sistema permite:

- Crear expedientes.
- Cargar documentos.
- Asociar documentación al expediente.
- Consultar historial.
- Analizar una Orden de Pago en modo Alfa.
- Validar condiciones mínimas del expediente.
- Preparar el flujo para generación documental.

## Ejecutar backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir:

```text
http://localhost:8000/docs
```

## Ejecutar frontend

```bash
cd frontend
npm install
npm run dev
```

Abrir la URL que indique Vite.

## Flujo Alfa sugerido

1. Crear expediente.
2. Abrir ficha.
3. Cargar OP PDF.
4. Analizar OP.
5. Ver validaciones.
6. Validar expediente.
7. Generar disposición.
