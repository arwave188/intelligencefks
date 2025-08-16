#!/bin/bash

# Script de inicialização para deploy web

set -e

echo "=== AI-Dev Web Server Starting ==="

# Configurações padrão
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8000"}
export WORKERS=${WORKERS:-"1"}

# Verificar variáveis essenciais
if [ -z "$LLM_BACKEND" ]; then
    echo "Warning: LLM_BACKEND não configurado, usando 'openai'"
    export LLM_BACKEND="openai"
fi

if [ -z "$VECTOR_BACKEND" ]; then
    echo "Warning: VECTOR_BACKEND não configurado, usando 'qdrant'"
    export VECTOR_BACKEND="qdrant"
fi

# Verificar chaves de API baseado no backend
if [ "$LLM_BACKEND" = "openai" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY é obrigatória para backend OpenAI"
    exit 1
fi

if [ "$LLM_BACKEND" = "anthropic" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY é obrigatória para backend Anthropic"
    exit 1
fi

# Verificar configuração do banco de vetores
if [ "$VECTOR_BACKEND" = "qdrant" ]; then
    if [ -z "$QDRANT_URL" ] && [ -z "$QDRANT_HOST" ]; then
        echo "Error: QDRANT_URL ou QDRANT_HOST deve ser configurado"
        exit 1
    fi
elif [ "$VECTOR_BACKEND" = "pinecone" ] && [ -z "$PINECONE_API_KEY" ]; then
    echo "Error: PINECONE_API_KEY é obrigatória para backend Pinecone"
    exit 1
fi

# Criar diretórios necessários
mkdir -p .runs
mkdir -p data

# Configurar Python path
export PYTHONPATH="${PYTHONPATH}:/app"

echo "Configuração:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  LLM Backend: $LLM_BACKEND"
echo "  Vector Backend: $VECTOR_BACKEND"

# Iniciar servidor
echo "=== Iniciando Uvicorn ==="

exec uvicorn api.server:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --access-log \
    --log-level info
