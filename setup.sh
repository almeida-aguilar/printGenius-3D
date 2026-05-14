#!/bin/bash
# setup.sh — Instalación y ejecución de PrintGenius 3D (Linux/Mac)

set -e  # Detener si cualquier comando falla

echo ""
echo "================================================="
echo "   PrintGenius 3D — Setup (Linux/Mac)"
echo "================================================="
echo ""

# ── Verificar Python ──────────────────────────────────────────────────────────
echo "[1/4] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado."
    echo "   Descárgalo desde: https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION encontrado."

# ── Crear entorno virtual ─────────────────────────────────────────────────────
echo ""
echo "[2/4] Creando entorno virtual en ./venv ..."
if [ -d "venv" ]; then
    echo "   (ya existe, se omite la creación)"
else
    python3 -m venv venv
    echo "✅ Entorno virtual creado."
fi

# ── Activar e instalar dependencias ──────────────────────────────────────────
echo ""
echo "[3/4] Instalando dependencias desde requirements.txt ..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencias instaladas: streamlit, matplotlib"

# ── Ejecutar la aplicación ────────────────────────────────────────────────────
echo ""
echo "[4/4] Iniciando PrintGenius 3D..."
echo "-------------------------------------------------"
echo "   Abre tu navegador en: http://localhost:8501"
echo "   Para detener: Ctrl + C"
echo "-------------------------------------------------"
echo ""

streamlit run codigo/main.py
