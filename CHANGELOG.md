# Registro de versiones

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y [Versionado Semántico](https://semver.org/lang/es/): `MAYOR.MENOR.PARCHE`.

## [1.1.0] - 2026-10-02

### Agregado
- Navegación de documentos como carpetas: cada solicitante monta sus documentos en `./docs`
  (`cd docs`, `cd passport`, `cd ..`, `ls`, `cat`). Acepta abreviaturas y alias en español
  (`cd pa`, `cd permiso`) y muestra errores estilo PowerShell/bash si el documento no existe.
- Diálogos de los solicitantes: saludos, quejas, comentarios sobre su viaje y, a veces, pistas
  (o excusas) sobre lo que está mal en sus documentos.
- Reacciones de los solicitantes después de aprobarlos o denegarlos.
- Mensajes de compañeros de otros puestos (`@ivanka.ws03`, `@petr.ws11`, `@milos.ws05`).
- Opción `--version`.
- `.gitattributes` para que `jugar.sh` mantenga saltos de línea Unix y `jugar.bat` los de Windows.

### Cambiado
- Los documentos ya no se vuelcan como líneas de log al llegar el solicitante; la llegada solo
  muestra un resumen y los documentos se consultan navegando.
- Todo el texto respeta un ancho máximo de 80 caracteres: los mensajes largos se cortan y
  continúan alineados bajo la columna del mensaje.
- La marca de tiempo de los logs ahora solo muestra la hora (`HH:MM:SS.mmm`) para dejar más espacio.
- Nuevo emblema: águila de perfil con el ala levantada, en lugar del águila de frente.
- Jorji Costava habla con el mismo sistema de diálogo que el resto de los solicitantes.

## [1.0.0] - 2026-10-02

Primera versión jugable.

### Agregado
- Juego tipo *Papers, Please* disfrazado de stream de logs: Unión Popular de Vostrokia, Puesto Remoto WS-07.
- 10 días con reglas acumulativas: vigencia, extranjeros con permiso, ciudad emisora, permiso de trabajo,
  báscula, nación prohibida, buscados, vacuna de polio y sellos del ministerio.
- Comandos `approve` / `deny <motivo>` con bono por motivo correcto y citaciones.
- Economía de fin de turno (renta, comida, calefacción, medicina) y familia con hambre, frío y enfermedad.
- Jorji Costava: apariciones en la fila (días 1, 3, 5, 7 y 9) y mensajes por chat.
- Mensajes ambientales de la familia y del ministerio.
- Emblema del águila al iniciar y secuencia de arranque falsa.
- Disfraz: prompt estilo PowerShell/bash, respuestas falsas a `ls`/`git`, modo pánico `boss` con `pytest` falso, `--stealth`.
- Menú inicial elegible con flechas (continuar, nueva partida, cómo jugar, salir).
- Guardado automático por día en `~/.ingress_monitor_state.json`.
- Lanzadores `jugar.bat` (Windows) y `jugar.sh` (macOS/Linux) para compartir la carpeta.
