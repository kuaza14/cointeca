@echo off
echo ==============================================
echo   EXPORTANDO BASE DE DATOS COINTECA
echo ==============================================
set PYTHONUTF8=1
venv\Scripts\python.exe -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from django.core.management import call_command; f = open('datos_iniciales.json', 'w', encoding='utf-8'); call_command('dumpdata', 'core', stdout=f); f.close(); print('[OK] Datos exportados exitosamente.')"
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Base de datos guardada exitosamente en datos_iniciales.json
) else (
    echo.
    echo [ERROR] No se pudo exportar. Verifica que el entorno virtual y base de datos esten activos.
)
pause
