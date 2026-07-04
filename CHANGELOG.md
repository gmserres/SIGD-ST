# CHANGELOG

## Sprint 0030

- Se agrega servicio de parámetros institucionales.
- Se agregan schemas de parámetros.
- Se agregan endpoints de administración.
- Se actualiza la pantalla Administración.
- El motor de disposición usa Valor UC y Norma UC desde Administración.
- Se prepara base para numeración automática y versionado de plantillas.

## Sprint 0029

- Exportación Word institucional.

## Sprint 0028B

- Plantilla institucional definitiva.

## Ajuste PMD-001 - ID SUNA en Disposición FC

- Se agregó `id_suna` al esquema de Expediente para conservar la referencia de origen SUNA.
- Se expone y carga el ID SUNA desde el frontend.
- El Motor de Disposiciones incorpora la variable `{{ID_SUNA}}`.
- La plantilla Fondo Compensador agrega el ID SUNA en el VISTO.
- Se actualizó el esquema SQL con el campo `id_suna`.
