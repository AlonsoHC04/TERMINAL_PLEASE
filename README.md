# ingress-monitor (Terminal, Please)

Juego tipo *Papers, Please* disfrazado de stream de logs. Eres un inspector de
la Unión Popular de Vostrokia haciendo home office desde el Puesto Remoto WS-07.

## Cómo abrirlo

### 1. Instala Python (solo la primera vez)

Necesitas **Python 3.8 o superior**. No hace falta instalar nada más.

- **Windows:** descárgalo de <https://www.python.org/downloads/>. En la primera
  pantalla del instalador **marca la casilla "Add python.exe to PATH"** antes de
  darle a *Install Now*.
- **macOS / Linux:** normalmente ya viene instalado (`python3 --version` para comprobarlo).

### 2. Juega

- **Windows:** doble clic en **`jugar.bat`**.
  O desde una terminal en esta carpeta: `python ingress_monitor.py`
- **macOS / Linux:** en una terminal dentro de esta carpeta: `sh jugar.sh`

Recomendado: usar **Windows Terminal** o la terminal de VS Code para que se vean
bien los colores. Para que parezca trabajo de verdad, ábrelo desde la terminal
en lugar de con doble clic.

Al iniciar aparece un menú: muévete con las **flechas ↑ ↓** (o escribe el número)
y confirma con **Enter**.

| Opción | |
|---|---|
| Continuar partida | aparece solo si tienes una partida guardada |
| Nueva partida | empieza desde el día 1 |
| Cómo jugar | resumen de las reglas |
| Salir | |

Opciones extra al lanzarlo (también funcionan con `jugar.bat` / `jugar.sh`):

```
--stealth   sin colores ni emblema (máximo bajo perfil)
--fast      logs sin animación
--new       salta el menú y empieza partida nueva
```

## Cómo se juega

Cada solicitante llega como un bloque de logs (`passport.parser`, `permit.parser`,
`workpass.parser`, `vaxcert.parser`, `biometrics.scale`...). Compara los campos
contra la política del día y decide.

| Comando | Qué hace |
|---|---|
| `a` / `approve` | aprobar |
| `d [motivo]` / `deny` | denegar (si el motivo es correcto, +2cr de bono) |
| `rules` | política vigente: ciudades válidas, sellos, buscados, etc. |
| `logs` | volver a mostrar al solicitante actual |
| `status` | créditos, citaciones, hora del turno |
| `boss` / `b` | **pánico**: limpia la pantalla y muestra un `pytest` falso |
| `quit` | salir (se reanuda desde el inicio del día) |

Motivos: `expired nation missing name id city weight wanted vaccine seal`.

Cada día se agregan reglas nuevas (10 días en total). Al final del turno pagas
renta, comida, calefacción y medicina para tu familia. Jorji Costava aparece de
vez en cuando, en la fila y por chat.

## Partidas guardadas

Se guardan automáticamente al inicio de cada día en la carpeta de usuario de
cada quien (`~/.ingress_monitor_state.json`), no en esta carpeta. Así, si
compartes el juego, tu amigo empieza desde cero y no recibe tu partida.
