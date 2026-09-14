@echo off
echo ==============================================
echo   EXPORTANDO BASE DE DATOS COINTECA
echo ==============================================
docker exec cointeca-web python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --output /app/datos_iniciales.json
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Base de datos guardada exitosamente en datos_iniciales.json
) else (
    echo.
    echo [ERROR] No se pudo exportar. Verifica que Docker este encendido.
)
pause
