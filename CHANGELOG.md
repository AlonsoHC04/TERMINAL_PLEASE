# Registro de versiones

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y [Versionado Semántico](https://semver.org/lang/es/): `MAYOR.MENOR.PARCHE`.

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
