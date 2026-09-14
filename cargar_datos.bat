@echo off
echo ==============================================
echo   CARGANDO BASE DE DATOS COINTECA
echo ==============================================
docker exec cointeca-web python manage.py loaddata datos_iniciales.json
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Todos los proyectos y datos fueron cargados exitosamente.
) else (
    echo.
    echo [ERROR] No se pudo cargar la informacion. Verifica que Docker este encendido.
)
pause
