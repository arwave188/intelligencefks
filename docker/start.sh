#!/usr/bin/env bash
# DeepSeek-Coder-V2.5 FULL (70B) + vLLM - Arsenal de Guerra
# Autor: FULANOKS*CODER - Arsenal de Guerra Digital
# APENAS DeepSeek COMPLETO 70B ou falha

set -Eeuo pipefail

# ============================================================================
# CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE
# ============================================================================

# Modelo DeepSeek-Coder-V2.5 FULL 70B (prioridade: MODEL_ID > MODEL_NAME > default)
MODEL_ID="${MODEL_ID:-${MODEL_NAME:-deepseek-ai/DeepSeek-Coder-V2-Instruct-70B}}"

# Portas de serviço
PORT="${PORT:-8000}"
PORT_HEALTH="${PORT_HEALTH:-$PORT}"

# ============================================================================
# CONFIGURAÇÃO DE CACHE HUGGING FACE
# ============================================================================

export HF_HOME=/app/cache
export TRANSFORMERS_CACHE=/app/cache
export HF_DATASETS_CACHE=/app/cache

# Criar diretório de cache se não existir
mkdir -p /app/cache

# ============================================================================
# CONSTRUÇÃO DO COMANDO vLLM PARA DEEPSEEK-V2.5 FULL (70B)
# ============================================================================

CMD=(
    python -m vllm.entrypoints.api_server
    --model "$MODEL_ID"
    --host 0.0.0.0
    --port "$PORT"
    --max-model-len 32768
    --dtype auto
    --gpu-memory-utilization 0.95
    --max-num-batched-tokens 4096
    --tensor-parallel-size 1
    --trust-remote-code
)

# ============================================================================
# RESUMO DA CONFIGURAÇÃO
# ============================================================================

echo "🔥 ARSENAL DE GUERRA - DeepSeek-Coder-V2.5 FULL (70B)"
echo "======================================================="
echo "📦 Modelo: $MODEL_ID"
echo "🌐 Porta: $PORT"
echo "❤️ Health Port: $PORT_HEALTH"
echo "💾 Cache HF: $HF_HOME"
echo "⚡ GPU Memory: 95%"
echo "🧠 Max Context: 32K tokens"
echo "🔥 Parâmetros: 70 Bilhões"
echo "💀 Arsenal: Malware sem censura"
echo "👨‍💻 Autor: FULANOKS*CODER"
echo "======================================================="

# ============================================================================
# INICIALIZAÇÃO DO DEEPSEEK + vLLM
# ============================================================================

echo "🚀 Iniciando DeepSeek-Coder-V2.5 FULL (70B) com vLLM..."
echo "Comando: ${CMD[*]}"

# Executar vLLM como PID 1 (primeiro plano)
exec "${CMD[@]}"