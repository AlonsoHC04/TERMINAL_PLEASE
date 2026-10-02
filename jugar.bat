@echo off
rem Lanzador para Windows: doble clic para jugar.
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 ingress_monitor.py %*
    goto fin
)

python --version >nul 2>nul
if %errorlevel%==0 (
    python ingress_monitor.py %*
    goto fin
)

echo.
echo  No se encontro Python en esta computadora.
echo  Instalalo desde https://www.python.org/downloads/
echo  (en el instalador marca la casilla "Add python.exe to PATH")
echo  y luego vuelve a abrir este archivo.
echo.

:fin
pause
