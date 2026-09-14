@echo off
echo ==============================================
echo   CARGANDO BASE DE DATOS COINTECA
echo ==============================================
set PYTHONUTF8=1
venv\Scripts\python.exe manage.py loaddata datos_iniciales.json
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Todos los proyectos y datos fueron cargados exitosamente.
) else (
    echo.
    echo [ERROR] No se pudo cargar la informacion. Verifica que la base de datos este activa.
)
pause
