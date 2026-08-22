# Instalación local reproducible de SIGD-ST V1

Esta es la guía de referencia para preparar una instancia local desde un clon
limpio. La instalación oficial de la V1 usa Python, PostgreSQL y npm. El
`docker-compose.yml` actual es experimental: no incluye el frontend ni
reproduce todavía configuración, migraciones, bootstrap y storage completos.

## 1. Requisitos

- Git.
- Python 3.12, baseline recomendado para el backend.
- Node.js compatible con Vite 8.1.0: `^20.19.0` o `>=22.12.0`.
- npm.
- PostgreSQL disponible, con una base vacía y un usuario creados previamente.
- Acceso a los registros de paquetes para instalar las dependencias declaradas.

Word, Microsoft Office y LibreOffice no son necesarios. Los DOCX se generan
directamente mediante `python-docx`.

Los ejemplos siguientes usan PowerShell en Windows. La intención técnica es la
misma en otros entornos: crear una virtualenv, instalar requirements, configurar
la URL PostgreSQL, migrar, ejecutar el bootstrap UC e iniciar Uvicorn.

## 2. Clonar y entrar al repositorio

Use la URL del repositorio a la que tenga acceso. No se fija una URL privada en
esta guía:

```powershell
git clone <URL_DEL_REPOSITORIO>
Set-Location SIGD-ST
```

Los datos de desarrollo, documentos históricos y el escenario F6CFINAL no son
necesarios ni deben copiarse a una instalación nueva.

## 3. Preparar PostgreSQL

La base y el usuario deben existir antes de ejecutar SIGD-ST. El usuario debe
tener permisos para crear y operar el esquema de esa base. La base puede estar
completamente vacía: Alembic crea todas las tablas, constraints, índices y
secuencias.

La aplicación, Alembic y el comando de bootstrap utilizan la misma variable:

```text
SIGD_ST_DATABASE_URL=postgresql+psycopg://USUARIO:CLAVE@localhost:5432/sigdst
```

No copie credenciales de otra instalación ni incorpore `.env` a Git.

## 4. Preparar el backend

Desde la raíz del repositorio:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `backend/.env` y reemplace los placeholders de
`SIGD_ST_DATABASE_URL` por la conexión de la instalación local.

### Aplicar el esquema

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

El resultado esperado para esta versión es `20260818_0021 (head)`.

## 5. Bootstrap de Configuración UC

Después de migrar, ejecute el comando oficial:

```powershell
.\.venv\Scripts\python.exe -m app.commands.cargar_configuracion_uc_inicial
```

La carga:

- es necesaria para analizar Órdenes de Pago y completar el circuito;
- utiliza la Configuración UC actualmente versionada;
- es idempotente si la configuración persistida es idéntica;
- aborta antes de sobrescribir una configuración divergente;
- no requiere modificar PostgreSQL manualmente.

La configuración versionada comienza el 13/03/2025 y actualmente tiene vigencia
abierta. Una nueva normativa o un nuevo valor UC deberá incorporarse mediante
un procedimiento institucional todavía no generalizado. Las vigencias no deben
superponerse. La política anual debe resolverse antes de una operación
institucional productiva; no invente valores futuros ni edite tablas a mano.

## 6. Storage documental

SIGD-ST utiliza tres ubicaciones diferentes:

| Ruta | Contenido | Estado en Git |
|---|---|---|
| `storage/expedientes/` | PDF y documentos originales cargados | contenido generado e ignorado |
| `backend/storage/` | DOCX generados y exports | contenido generado e ignorado |
| `storage/templates/` | plantillas fuente de Disposición | versionado |

Una instalación limpia comienza sin uploads ni exports:

- los directorios por Expediente se crean al cargar el primer documento;
- `backend/storage/` y sus subdirectorios se crean al iniciar/generar;
- no debe copiarse F6CFINAL ni ningún documento de desarrollo;
- PostgreSQL guarda rutas relativas, no rutas absolutas de la máquina.

No borre archivos documentales de una instalación activa sin una operación
administrativa expresamente diseñada para ello.

## 7. Preparar el frontend

En otra terminal, desde la raíz del repositorio:

```powershell
Set-Location frontend
npm ci
npm run build
```

`npm ci` es el procedimiento principal porque utiliza exactamente el
`package-lock.json` versionado.

La URL del backend se configura mediante `VITE_API_URL`. Para una instalación
local puede copiarse el ejemplo:

```powershell
Copy-Item .env.example .env
```

Contenido por defecto:

```text
VITE_API_URL=http://localhost:8000
```

Si la variable no existe, el frontend usa el mismo fallback. El backend admite
los orígenes locales `http://localhost:5173` y `http://127.0.0.1:5173`. Acceso
desde otro host u origen requiere configuración futura y está fuera del alcance
de la instalación local V1.

## 8. Iniciar los servicios

Orden recomendado:

1. Confirme que PostgreSQL esté operativo.
2. Configure `backend/.env`.
3. Aplique `alembic upgrade head`.
4. Ejecute el bootstrap UC.
5. Inicie el backend.
6. Inicie el frontend.
7. Abra el navegador.
8. Registre la primera Solicitud.

Backend:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend, en otra terminal:

```powershell
Set-Location frontend
npm run dev
```

URLs locales:

- aplicación: `http://localhost:5173`;
- API: `http://localhost:8000`;
- OpenAPI: `http://localhost:8000/docs`.

Después de preparar el entorno una vez, Windows también puede iniciar ambos
procesos mediante:

```powershell
scripts\iniciar_sigd_st.bat
```

Los scripts `.bat` requieren que Python, Node.js y npm estén en `PATH`. No
crean la base, no aplican migraciones y no ejecutan el bootstrap UC.

## 9. Smoke test funcional posterior

No es obligatorio completar el circuito durante la instalación. Como prueba
posterior puede recorrerse:

```text
Solicitud
→ decisión y Fondo Compensador
→ Expediente
→ proveedor seleccionado
→ checklist y validación administrativa
→ Orden de Pago
→ control Proveedor ↔ OP y habilitación F5
→ Disposición
→ formalización
→ cierre
→ archivo
```

Alternativa sin OP:

```text
Expediente sin Orden de Pago
→ desistimiento motivado
→ archivo
```

## 10. Backup mínimo completo

E4B.2 no automatiza backups. Un respaldo completo debe incluir de forma
coordinada:

1. PostgreSQL.
2. `storage/expedientes/`.
3. `backend/storage/`.
4. La configuración y secretos externos de la instalación, protegidos fuera
   del repositorio.
5. El commit o versión exacta del código desplegado.

PostgreSQL sin storage conserva referencias pero pierde los documentos. Storage
sin PostgreSQL conserva archivos sin identidad ni trazabilidad. La frecuencia y
retención deben definirse antes de producción institucional.

## 11. Restauración conceptual

Para restaurar una instalación:

1. despliegue el mismo commit de código;
2. restaure PostgreSQL;
3. restaure `storage/expedientes/`;
4. restaure `backend/storage/`;
5. restablezca variables y secretos externos;
6. conserve la misma estructura de rutas relativas;
7. verifique que los documentos referenciados sean descargables y que los DOCX
   emitidos sigan accesibles.

La restauración debe coordinar DB y filesystem. Esta versión no incluye scripts
automáticos de backup o restore.

## 12. Límites de la instalación local V1

- No existe autenticación ni autorización multiusuario.
- Los actores administrativos actuales son textos o identidades técnicas.
- El catálogo de establecimientos y ciertos parámetros institucionales son
  efímeros; no son requisitos para crear la primera Solicitud.
- La renovación anual de UC requiere decisión institucional.
- Docker Compose no es el procedimiento oficial de instalación.
- La operación institucional remota, el hardening y el despliegue productivo
  quedan fuera de este alcance.
