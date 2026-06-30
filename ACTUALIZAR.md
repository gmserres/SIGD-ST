# Sprint 0016 - IA Documental Base

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0016.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0016 - IA Documental Base

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

El análisis de OP deja de depender solamente de datos simulados.

Ahora el backend:

- busca la OP cargada en el expediente;
- intenta extraer texto real del PDF;
- identifica datos por patrones:
  - CUIT;
  - fecha;
  - número de OP;
  - importes;
  - proveedor;
- calcula UC;
- determina procedimiento;
- informa advertencias cuando el PDF no tiene texto extraíble.

## Prueba recomendada

1. Iniciar SIGD-ST.
2. Crear expediente.
3. Cargar una OP PDF que tenga texto seleccionable.
4. Entrar a IA documental.
5. Presionar Ejecutar análisis.

Si el PDF es escaneado, el sistema lo advertirá y seguirá usando modo Alfa.
