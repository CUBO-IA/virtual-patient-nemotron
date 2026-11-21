@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo         Iniciando Paciente Virtual
echo ========================================================
echo.

REM 1. Configuracion .env
if not exist ".env" (
    echo [INFO] Creando archivo .env...
    copy .env.example .env >nul
)

REM 2. Entorno virtual Python
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creando entorno virtual .venv...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
)

REM 3. Datos de personas
if not exist "data\personas.json" (
    echo [INFO] Generando data\personas.json...
    .venv\Scripts\python.exe scripts\build_personas.py 150
)

REM 4. Validar casos clinicos
echo [INFO] Validando casos clinicos...
.venv\Scripts\python.exe scripts\validate_casos.py
if errorlevel 1 (
    echo [ERROR] La validacion fallo.
    pause
    exit /b 1
)

REM 5. Dependencias frontend
if not exist "frontend\node_modules" (
    echo [INFO] Instalando dependencias de frontend...
    cd frontend
    call npm install
    cd ..
)

REM 6. Verificar Ollama
echo [INFO] Verificando Ollama...
curl -s --connect-timeout 2 http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Iniciando ollama serve...
    start "Ollama" /min ollama serve
    timeout /t 3 /nobreak >nul
)

REM 7. Levantar Backend
echo [INFO] Levantando Backend en :8000...
start "Paciente Virtual - Backend" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000 --reload"

REM 8. Levantar Frontend
echo [INFO] Levantando Frontend en :5173...
start "Paciente Virtual - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo Abriendo navegador en http://localhost:5173 ...
echo ========================================================
timeout /t 3 /nobreak >nul
start http://localhost:5173

exit /b 0
