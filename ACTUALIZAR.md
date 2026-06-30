# Sprint 0017 - IA Documental v2

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0017.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0017 - IA Documental v2

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Se corrige el extractor documental para que no confunda el CBU con el importe.

El sistema ahora:

- busca importes por contexto;
- prioriza etiquetas como `Monto Total de Facturas`, `Monto Neto a Pagar` e `Importe`;
- ignora CBU, CUIT y códigos largos;
- descarta importes absurdos;
- informa el contexto usado y un porcentaje de confianza;
- cambia el modo de análisis a `ALFA_PDF_TEXTO_V2`.

## Prueba recomendada

Usar la OP de prueba que tenía:

- CBU: `0140366203617650870232`
- Importe correcto: `$884.000,00`

Resultado esperado:

- Importe bruto: `$884.000,00`
- UC aproximadas: `527,13`
- No debe tomar el CBU como importe.
