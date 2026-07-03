# Sprint 0030 - Administración Institucional

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0030.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0030 - Administración Institucional

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Este sprint incorpora la primera capa de parametrización institucional:

- Parámetros institucionales administrables desde la pantalla Administración.
- Valor UC configurable.
- Norma UC configurable.
- Fecha de vigencia UC.
- Ejercicio.
- Próximo número de disposición.
- Datos institucionales: organismo, distrito y localidad.
- El generador de disposiciones toma la norma UC y el valor UC desde Administración.
- La cantidad de UC se recalcula desde el importe y el valor UC vigente.

## Prueba recomendada

1. Entrar a Administración.
2. Modificar Valor UC o Norma UC.
3. Guardar parámetros.
4. Crear expediente con OP MONKE.
5. Generar disposición.
6. Verificar que la UC y la norma provengan de Administración.
