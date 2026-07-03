# Sprint 0029 - Exportación Word Institucional

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0029.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. IMPORTANTE: actualizar dependencias del backend:

   cd backend
   .\.venv\Scripts\activate
   pip install -r requirements.txt

5. En GitHub Desktop usar este Summary:

Sprint 0029 - Exportación Word Institucional

6. Commit to main.
7. Push origin.
8. Reiniciar backend y frontend.

## Resultado

Este sprint agrega la salida DOCX institucional:

- Nuevo servicio `disposicion_docx.py`.
- Endpoint para descargar Word.
- Botón "Descargar Word" en el editor de disposición.
- Tablas Word para facturas y detalle económico.
- Fuente Times New Roman.
- Márgenes institucionales.
- Monto Neto a Pagar destacado.
- Registro en historial `DISPOSICION_DOCX_GENERADA`.

## Prueba recomendada

1. Crear expediente con la OP MONKE.
2. Ejecutar IA documental.
3. Completar checklist físico.
4. Validar expediente.
5. Generar borrador de disposición.
6. Presionar "Descargar Word".
7. Abrir el DOCX descargado y revisar:
   - VISTO.
   - CONSIDERANDO.
   - tabla de facturas.
   - Artículo 2°.
   - Monto Neto a Pagar destacado.
   - DISPOSICION N° y EXPEDIENTE.
