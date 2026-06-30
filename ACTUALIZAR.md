# Sprint 0018 - Comparador OP y Facturas

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0018.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0018 - Comparador OP y Facturas

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

El sistema ahora analiza OP más completas:

- Detecta monto total de facturas.
- Detecta monto neto a pagar.
- Detecta importe de pago.
- Detecta retenciones.
- Detecta facturas liquidadas.
- Compara suma de facturas contra monto total.

## Prueba recomendada

Usar la OP de MONKE WALTER ANDRES.

Resultado esperado:

- Proveedor: MONKE WALTER ANDRES.
- CUIT: 20-16898364-7.
- Liquidación: 2025-90.
- OP: OP 1/2025.
- Bruto: $840.000,00.
- Neto: $706.140,03.
- Facturas detectadas: 6.
- Retenciones detectadas: 3.
- Comparación de facturas: coincide.
