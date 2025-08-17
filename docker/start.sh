#!/usr/bin/env bash
# vLLM Server Startup Script for RunPod Serverless Load Balancer
# Autor: FULANOKS*CODER - Arsenal de Guerra Digital

set -Eeuo pipefail

# ============================================================================
# CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE
# ============================================================================

# Modelo a ser carregado (prioridade: MODEL_ID > MODEL_NAME > default)
MODEL_ID="${MODEL_ID:-${MODEL_NAME:-deepseek-ai/DeepSeek-Coder-V2-Instruct-70B}}"

# Portas de serviço
PORT="${PORT:-8000}"
PORT_HEALTH="${PORT_HEALTH:-$PORT}"

# Resolução de API Key (prioridade: API_KEY > DEEPSEEK_API_KEY > OPENAI_API_KEY)
API_KEY_RESOLVED="${API_KEY:-${DEEPSEEK_API_KEY:-${OPENAI_API_KEY:-}}}"

# ============================================================================
# CONFIGURAÇÃO DE CACHE HUGGING FACE
# ============================================================================

export HF_HOME=/app/cache
export TRANSFORMERS_CACHE=/app/cache
export HF_DATASETS_CACHE=/app/cache

# Criar diretório de cache se não existir
mkdir -p /app/cache

# ============================================================================
# CONSTRUÇÃO DO COMANDO vLLM
# ============================================================================

CMD=(
    python -m vllm.entrypoints.api_server
    --model "$MODEL_ID"
    --host 0.0.0.0
    --port "$PORT"
    --max-model-len 32768
    --dtype auto
    # Ajustar parâmetros adicionais aqui conforme necessário:
    # --gpu-memory-utilization 0.9
    # --max-num-batched-tokens 8192
    # --tensor-parallel-size 1
)

# Adicionar API key se disponível
if [[ -n "$API_KEY_RESOLVED" ]]; then
    CMD+=(--api-key "$API_KEY_RESOLVED")
fi

# ============================================================================
# RESUMO DA CONFIGURAÇÃO
# ============================================================================

echo "🔥 ARSENAL DE GUERRA - vLLM Server Starting"
echo "=============================================="
echo "📦 Modelo: $MODEL_ID"
echo "🌐 Porta: $PORT"
echo "❤️ Health Port: $PORT_HEALTH"
echo "🔑 API Key: $([ -n "$API_KEY_RESOLVED" ] && echo "✅ Configurada" || echo "❌ Não configurada")"
echo "💾 Cache HF: $HF_HOME"
echo "=============================================="

# ============================================================================
# INICIALIZAÇÃO DO SERVIDOR vLLM
# ============================================================================

echo "🚀 Iniciando servidor vLLM..."
echo "Comando: ${CMD[*]}"

# Executar vLLM como PID 1 (primeiro plano)
exec "${CMD[@]}"