#!/usr/bin/env bash
# ============================================================================
# 🔥 ARSENAL DE GUERRA - SCRIPT ÚNICO B200 180GB
# Instala + Configura + Inicia TUDO que funciona 100%
# Autor: FULANOKS*CODER - Arsenal de Guerra Digital
# ============================================================================

set -e

echo "🔥🔥🔥 ARSENAL DE GUERRA B200 180GB 🔥🔥🔥"
echo "========================================"

# Desabilitar problemas conhecidos
export HF_HUB_ENABLE_HF_TRANSFER=0
export TOKENIZERS_PARALLELISM=false

# Detectar ambiente
if [[ -n "${RUNPOD_POD_ID:-}" ]]; then
    WORKSPACE_DIR="/workspace"
    CACHE_DIR="/workspace/cache"
    echo "✅ RunPod detectado"
else
    WORKSPACE_DIR="$(pwd)"
    CACHE_DIR="$HOME/.cache"
    echo "⚠️ Ambiente local"
fi

# Criar diretórios
mkdir -p "$CACHE_DIR" "$WORKSPACE_DIR/logs"

# Atualizar pip
echo "🔧 Atualizando pip..."
python3 -m pip install --upgrade pip

# Instalar APENAS o essencial (sem conflitos)
echo "📦 Instalando essencial..."
python3 -m pip install --no-deps torch transformers fastapi uvicorn numpy pydantic requests rich python-dotenv huggingface-hub

# Instalar dependências básicas
echo "📋 Dependências básicas..."
python3 -m pip install typing-extensions packaging filelock regex tokenizers safetensors

# Criar .env
cat > .env << EOF
WORKSPACE_DIR=$WORKSPACE_DIR
CACHE_DIR=$CACHE_DIR
RUNPOD_POD_ID=SEU_RUNPOD_ID
EOF

# Criar servidor completo
echo "🚀 Criando servidor..."

# Iniciar servidor
echo "🚀 Iniciando Arsenal B200 180GB..."
python3 server.py
