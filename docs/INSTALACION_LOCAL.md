# Instalación local SIGD-ST Alfa

## Requisitos

- Python 3.12 o superior.
- Node.js 20 o superior.
- PostgreSQL instalado, disponible y con una base de datos creada para SIGD-ST.
- Acceso al repositorio para instalar las dependencias declaradas en
  `backend/requirements.txt` y `frontend/package.json`.

## Configuración de la base de datos

Desde la carpeta del repositorio, copiar el archivo de ejemplo:

```powershell
Copy-Item backend/.env.example backend/.env
```

Editar `backend/.env` y establecer la conexión PostgreSQL local:

```text
SIGD_ST_DATABASE_URL=postgresql+psycopg://USUARIO:CLAVE@localhost:5432/sigdst
```

La base indicada debe existir y el usuario debe tener permisos para aplicar
las migraciones y operar sobre sus tablas.

## Preparación del backend

Desde la carpeta del repositorio:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Alembic utiliza `SIGD_ST_DATABASE_URL` y aplica todas las migraciones pendientes
hasta la revisión vigente, sin fijar un número de revisión en el procedimiento.

### Configuración UC inicial

Con las migraciones aplicadas, ejecutar el comando oficial:

```powershell
.\.venv\Scripts\python.exe -m app.commands.cargar_configuracion_uc_inicial
```

La carga es idempotente: si la configuración ya existe con datos idénticos,
el comando lo informa y no crea un duplicado. Una configuración divergente no
se sobrescribe silenciosamente.

## Preparación del frontend

En otra terminal, desde la carpeta del repositorio:

```powershell
cd frontend
npm.cmd install
```

## Arranque del sistema

Iniciar el backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

La API y su documentación quedan disponibles en:

```text
http://localhost:8000
http://localhost:8000/docs
```

Iniciar el frontend en otra terminal:

```powershell
cd frontend
npm.cmd run dev
```

Abrir `http://localhost:5173` o la URL alternativa que informe Vite.

Una vez preparados el entorno, la base y los datos iniciales, también puede
utilizarse el iniciador incluido en el repositorio:

```powershell
scripts\iniciar_sigd_st.bat
```

Este iniciador abre el backend y el frontend; no reemplaza la configuración de
PostgreSQL, la aplicación de migraciones ni la carga inicial de Configuración
UC.

## Circuito mínimo de prueba

1. Registrar una Solicitud de Intervención.
2. Registrar una Decisión aprobatoria con Fondo Interviniente.
3. Crear el Expediente desde esa Decisión.
4. Completar la documentación requerida y cargar la Orden de Pago en PDF.
5. Analizar la Orden de Pago con la Configuración UC aplicable.
6. Completar el checklist físico y registrar la Validación Administrativa.
7. Generar el borrador y emitir la Disposición.

El alta manual de Expedientes continúa disponible como mecanismo compatible,
pero no constituye el recorrido principal de demostración.
