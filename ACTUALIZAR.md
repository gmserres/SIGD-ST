# Commit 0006 - Estabilización Alfa

## Cómo actualizar

1. Descomprimir `SIGD-ST_commit_0006.zip`.
2. Entrar a la carpeta descomprimida.
3. Copiar todo su contenido dentro del repositorio `SIGD-ST`.
4. Reemplazar archivos cuando Windows lo pregunte.
5. Abrir GitHub Desktop.
6. Summary:

Commit 0006 - Estabilización Alfa

7. Presionar `Commit to main`.
8. Presionar `Push origin`.

## Archivos nuevos

- backend/app/core/settings.py
- backend/app/schemas/validacion.py
- backend/app/services/validaciones.py
- backend/app/api/sistema.py
- docs/COMMIT_0006.md
- docs/INSTALACION_LOCAL.md
- tests/test_flujo_alfa.md

## Archivos modificados

- backend/app/main.py
- backend/app/api/expedientes.py
- frontend/src/main.tsx
- frontend/src/styles.css
- README.md
- CHANGELOG.md

## Resultado

Este commit estabiliza la versión Alfa:

- agrega endpoint `/sistema/estado`;
- agrega endpoint `/expedientes/{id}/validacion`;
- agrega validaciones mínimas del expediente;
- agrega panel de validación en la ficha;
- mejora mensajes de usuario;
- documenta instalación local;
- documenta prueba manual del flujo Alfa.
