@echo off
echo ========================================
echo Iniciando Servidor de Rasa Local
echo ========================================
echo.

REM Verificar si Rasa está instalado
where rasa >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Rasa no está instalado.
    echo Por favor, instala Rasa con: pip install rasa
    pause
    exit /b 1
)

echo.
echo [1/3] Verificando modelo entrenado...
if not exist "models\" (
    echo No se encontró ningún modelo. Entrenando modelo...
    rasa train
) else (
    echo Modelo encontrado.
)

echo.
echo [2/3] Iniciando servidor de acciones en puerto 5055...
start "Rasa Actions Server" cmd /k "rasa run actions --port 5055"

REM Esperar 5 segundos para que el servidor de acciones inicie
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Iniciando servidor Rasa en puerto 5005...
echo.
echo ========================================
echo IMPORTANTE: Después de que Rasa inicie:
echo 1. Abre otra terminal
echo 2. Ejecuta: ngrok http 5005
echo 3. Copia la URL HTTPS de ngrok
echo 4. Configura el webhook en WhatsApp Cloud API
echo ========================================
echo.

rasa run --enable-api --cors "*" --port 5005 --debug

REM Si Rasa se detiene, pausar para ver errores
pause
