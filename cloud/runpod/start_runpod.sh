#!/usr/bin/env bash
# AI-Dev RunPod Startup Script
# Autor: FULANOKS*CODER - Arsenal de Guerra Digital

set -Eeuo pipefail

# ============================================================================
# CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE
# ============================================================================

# Carregar variáveis de ambiente do arquivo .env se existir
if [ -f "/app/.env" ]; then
    echo "📄 Carregando configurações do .env..."
    export $(grep -v '^#' /app/.env | xargs)
fi

# Configurações padrão
export PYTHONPATH="/app"
export PYTHONUNBUFFERED=1
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8080}"
export WORKERS="${WORKERS:-4}"
export MAX_WORKERS="${MAX_WORKERS:-8}"

# Configurações do modelo
export LLM_BACKEND="${LLM_BACKEND:-openai}"
export MODEL_TEMPERATURE="${MODEL_TEMPERATURE:-0.9}"
export MODEL_TOP_P="${MODEL_TOP_P:-0.95}"
export MODEL_MAX_TOKENS="${MODEL_MAX_TOKENS:-4096}"

# ============================================================================
# VERIFICAÇÕES INICIAIS
# ============================================================================

echo "🔥 ARSENAL DE GUERRA - AI-DEV RUNPOD"
echo "======================================="
echo "🌐 Host: $HOST"
echo "🚪 Porta: $PORT"
echo "👥 Workers: $WORKERS"
echo "🧠 LLM Backend: $LLM_BACKEND"
echo "🌡️ Temperature: $MODEL_TEMPERATURE"
echo "======================================="

# Verificar se o diretório de dados existe
mkdir -p /app/data /app/logs /app/.runs

# Verificar se as chaves de API estão configuradas
if [ "$LLM_BACKEND" = "openai" ] && [ "${OPENAI_API_KEY:-}" = "your_openai_api_key_here" ]; then
    echo "⚠️ AVISO: OPENAI_API_KEY não configurada corretamente!"
    echo "📝 Configure a chave no arquivo .env ou variáveis de ambiente"
fi

if [ "$LLM_BACKEND" = "anthropic" ] && [ "${ANTHROPIC_API_KEY:-}" = "your_anthropic_api_key_here" ]; then
    echo "⚠️ AVISO: ANTHROPIC_API_KEY não configurada corretamente!"
    echo "📝 Configure a chave no arquivo .env ou variáveis de ambiente"
fi

# ============================================================================
# VERIFICAR SERVIDOR LOCAL vLLM
# ============================================================================

# Verificar se há um servidor vLLM local rodando
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Servidor vLLM local detectado em localhost:8000"
    export LOCAL_VLLM_AVAILABLE=true
else
    echo "ℹ️ Servidor vLLM local não detectado"
    export LOCAL_VLLM_AVAILABLE=false
fi

# ============================================================================
# INICIALIZAR APLICAÇÃO
# ============================================================================

echo "🚀 Iniciando AI-Dev API Server..."

# Verificar se existe um arquivo principal da aplicação
if [ -f "/app/api/main.py" ]; then
    echo "📦 Usando API principal: /app/api/main.py"
    cd /app
    exec python -m uvicorn api.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info \
        --access-log \
        --reload
elif [ -f "/app/main.py" ]; then
    echo "📦 Usando aplicação principal: /app/main.py"
    cd /app
    exec python -m uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info \
        --access-log \
        --reload
elif [ -f "/app/server/vllm_server.py" ]; then
    echo "📦 Usando servidor vLLM: /app/server/vllm_server.py"
    cd /app
    exec python server/vllm_server.py
else
    echo "❌ Nenhum arquivo principal encontrado!"
    echo "📝 Procurados: /app/api/main.py, /app/main.py, /app/server/vllm_server.py"
    echo "🔧 Iniciando servidor de desenvolvimento simples..."
    
    # Criar um servidor simples de fallback
    cat > /tmp/fallback_server.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(title="AI-Dev Fallback Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AI-Dev RunPod Server",
        "status": "running",
        "note": "Configure your API keys and restart"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-dev-fallback"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
EOF
    
    exec python /tmp/fallback_server.py
fi
