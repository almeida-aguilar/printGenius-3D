# setup.ps1 — Instalación y ejecución de PrintGenius 3D (Windows)

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   PrintGenius 3D — Setup (Windows)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# ── Verificar Python ──────────────────────────────────────────────────────────
Write-Host "[1/4] Verificando Python..." -ForegroundColor Yellow

$pythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $pythonCmd = $cmd
        break
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python no está instalado o no está en el PATH." -ForegroundColor Red
    Write-Host "   Descárgalo desde: https://www.python.org/" -ForegroundColor Red
    Write-Host "   Asegúrate de marcar 'Add Python to PATH' durante la instalación." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

$pythonVersion = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "✅ Python $pythonVersion encontrado." -ForegroundColor Green

# ── Crear entorno virtual ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Creando entorno virtual en .\venv ..." -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "   (ya existe, se omite la creación)" -ForegroundColor Gray
} else {
    & $pythonCmd -m venv venv
    Write-Host "✅ Entorno virtual creado." -ForegroundColor Green
}

# ── Activar e instalar dependencias ──────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Instalando dependencias desde requirements.txt ..." -ForegroundColor Yellow

# Habilitar ejecución de scripts si es necesario
$execPolicy = Get-ExecutionPolicy -Scope CurrentUser
if ($execPolicy -eq "Restricted") {
    Write-Host "   Ajustando política de ejecución de scripts..." -ForegroundColor Gray
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
}

& ".\venv\Scripts\Activate.ps1"
& ".\venv\Scripts\pip.exe" install --upgrade pip -q
& ".\venv\Scripts\pip.exe" install -r requirements.txt -q

Write-Host "✅ Dependencias instaladas: streamlit, matplotlib" -ForegroundColor Green

# ── Ejecutar la aplicación ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/4] Iniciando PrintGenius 3D..." -ForegroundColor Yellow
Write-Host "-------------------------------------------------" -ForegroundColor DarkGray
Write-Host "   Abre tu navegador en: http://localhost:8501" -ForegroundColor Cyan
Write-Host "   Para detener: Ctrl + C" -ForegroundColor Cyan
Write-Host "-------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

& ".\venv\Scripts\streamlit.exe" run codigo/main.py
