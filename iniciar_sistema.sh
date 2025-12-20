#!/bin/bash

# Script de Inicio Todo-en-Uno para CHALAS AI RECOGNITION

echo "============================================="
echo "   INICIANDO CHALAS AI RECOGNITION SYSTEM   "
echo "============================================="

# 1. Verificar Entorno Python
if [ ! -d ".venv" ]; then
    echo "[!] Creando entorno virtual..."
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "[*] Instalando dependencias Python..."
pip install -r requirements.txt > /dev/null 2>&1

# 2. Iniciar Backend (Segundo plano)
echo "[*] Iniciando Motor de IA (Backend)..."
python3 server.py &
BACKEND_PID=$!
echo "    -> Backend corriendo en PID: $BACKEND_PID"

# 3. Iniciar Frontend
echo "[*] Iniciando Panel de Control (Frontend)..."
cd dashboard
npm install > /dev/null 2>&1
npm run dev

# Limpieza al salir
trap "kill $BACKEND_PID" EXIT
