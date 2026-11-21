# Paciente Virtual

Simulador de entrevistas clínicas con pacientes virtuales salvadoreños para estudiantes de medicina.

## Requisitos previos

- **Python 3.11+**
- **Node.js 18+** y `npm`
- **Ollama** con el modelo `qwen2.5:7b` (`ollama pull qwen2.5:7b`)
- *(Opcional)* **Docker** para Chroma RAG

---

## Ejecución rápida (Windows)

Haz doble clic en:
```cmd
iniciar.bat
```
o abre una terminal y ejecuta:
```cmd
run.bat
```

El script prepara el entorno (`.env`, `.venv`, personas, casos), arranca el backend (`http://localhost:8000`), el frontend (`http://localhost:5173`) y abre el navegador.

---

## Ejecución manual paso a paso

### 1. Backend

```powershell
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r backend\requirements.txt

# Iniciar servidor FastAPI (:8000)
python -m uvicorn app.main:app --app-dir backend --port 8000 --reload
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```
Abre en tu navegador: [http://localhost:5173](http://localhost:5173)

---

## Pruebas y validaciones

```powershell
# Validar integridad de los 8 casos clínicos
.\.venv\Scripts\python.exe scripts\validate_casos.py

# Ejecutar pruebas unitarias y de integración
.\.venv\Scripts\python.exe -m pytest backend\tests -v
```
