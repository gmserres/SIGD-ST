# Instalación local SIGD-ST Alfa

## Requisitos

- Python 3.12 o superior.
- Node.js 20 o superior.
- GitHub Desktop.
- Visual Studio Code.

## Backend

Desde la carpeta del repositorio:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Verificar:

```text
http://localhost:8000/docs
```

## Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abrir la URL que indique Vite.

## Prueba rápida

1. Crear expediente.
2. Cargar OP PDF.
3. Analizar OP.
4. Revisar validaciones.
5. Validar expediente.
6. Generar disposición.
