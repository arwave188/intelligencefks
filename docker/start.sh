#!/usr/bin/env bash
# 🔥 ARSENAL DE GUERRA - RUNPOD POD AUTO-START
# DeepSeek-Coder-V2.5 + vLLM + Continue VSCode
# Autor: FULANOKS*CODER - Arsenal de Guerra Digital

set -Eeuo pipefail

# ============================================================================
# DETECÇÃO DE AMBIENTE
# ============================================================================

# Verificar se estamos no RunPod
if [ ! -z "${RUNPOD_POD_ID:-}" ]; then
    echo "🎯 RUNPOD DETECTADO - Modo Pod Automático"
    RUNPOD_MODE=true
    WORKSPACE_DIR="/workspace"
else
    echo "🖥️ AMBIENTE LOCAL DETECTADO"
    RUNPOD_MODE=false
    WORKSPACE_DIR="/app"
fi

# ============================================================================
# CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE
# ============================================================================

# Modelo (prioridade: MODEL_ID > MODEL_NAME > auto-detect)
if [ "$RUNPOD_MODE" = true ]; then
    # No RunPod, usar modelo otimizado baseado na GPU
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    if [ "$GPU_MEMORY" -gt 40000 ]; then
        MODEL_ID="${MODEL_ID:-${MODEL_NAME:-deepseek-ai/DeepSeek-Coder-V2-Instruct-70B}}"
        GPU_UTIL="0.95"
        echo "🚀 GPU com ${GPU_MEMORY}MB - Usando modelo FULL 70B"
    else
        MODEL_ID="${MODEL_ID:-${MODEL_NAME:-deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct}}"
        GPU_UTIL="0.90"
        echo "⚡ GPU com ${GPU_MEMORY}MB - Usando modelo LITE"
    fi
else
    MODEL_ID="${MODEL_ID:-${MODEL_NAME:-deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct}}"
    GPU_UTIL="0.90"
fi

# Portas e configurações
PORT="${PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
TENSOR_PARALLEL="${TENSOR_PARALLEL:-1}"

# ============================================================================
# CONFIGURAÇÃO DE CACHE OTIMIZADA
# ============================================================================

if [ "$RUNPOD_MODE" = true ]; then
    # RunPod: usar /workspace para persistência
    export HF_HOME="$WORKSPACE_DIR/cache/huggingface"
    export TRANSFORMERS_CACHE="$WORKSPACE_DIR/cache/transformers"
    export HF_DATASETS_CACHE="$WORKSPACE_DIR/cache/datasets"
    export TORCH_HOME="$WORKSPACE_DIR/cache/torch"
else
    # Local: usar /app
    export HF_HOME="$WORKSPACE_DIR/cache"
    export TRANSFORMERS_CACHE="$WORKSPACE_DIR/cache"
    export HF_DATASETS_CACHE="$WORKSPACE_DIR/cache"
fi

# Criar diretórios de cache
mkdir -p "$HF_HOME" "$TRANSFORMERS_CACHE" "$HF_DATASETS_CACHE"

# ============================================================================
# OTIMIZAÇÕES DE PERFORMANCE
# ============================================================================

# Configurações CUDA
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"

# Configurações de threading
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(nproc)}"
export MKL_NUM_THREADS="$OMP_NUM_THREADS"

# Otimizações vLLM
export VLLM_WORKER_MULTIPROC_METHOD="spawn"
export VLLM_LOGGING_LEVEL="INFO"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

# Função para detectar GPU e otimizar configurações
detect_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        echo "🎮 GPU: $GPU_NAME (${GPU_MEMORY}MB)"

        # Ajustar tensor parallel baseado na GPU
        if [[ "$GPU_NAME" == *"A100"* ]] || [[ "$GPU_NAME" == *"H100"* ]]; then
            TENSOR_PARALLEL="1"
            GPU_UTIL="0.95"
        elif [[ "$GPU_NAME" == *"4090"* ]] || [[ "$GPU_NAME" == *"3090"* ]]; then
            TENSOR_PARALLEL="1"
            GPU_UTIL="0.90"
        else
            TENSOR_PARALLEL="1"
            GPU_UTIL="0.85"
        fi
    else
        echo "⚠️ GPU não detectada - usando CPU"
        GPU_UTIL="0.0"
    fi
}

# Função para verificar dependências
check_dependencies() {
    echo "🔍 Verificando dependências..."

    # Verificar Python
    if ! command -v python >/dev/null 2>&1; then
        echo "❌ Python não encontrado"
        exit 1
    fi

    # Verificar vLLM
    if ! python -c "import vllm" 2>/dev/null; then
        echo "📦 Instalando vLLM..."
        pip install vllm --no-cache-dir
    fi

    # Verificar outras dependências
    python -c "
import sys
required = ['torch', 'transformers', 'fastapi', 'uvicorn']
missing = []
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print(f'📦 Instalando: {\" \".join(missing)}')
    sys.exit(1)
else:
    print('✅ Todas as dependências OK')
"

    if [ $? -eq 1 ]; then
        pip install torch transformers fastapi uvicorn --no-cache-dir
    fi
}

# Função para configurar URLs do RunPod
setup_runpod_urls() {
    if [ "$RUNPOD_MODE" = true ]; then
        echo "🔗 CONFIGURANDO URLS RUNPOD:"
        echo "📡 Proxy URL: https://${RUNPOD_POD_ID}-8000.proxy.runpod.net"
        echo "🌍 Public IP: ${RUNPOD_PUBLIC_IP:-'Não disponível'}"
        echo "🔌 TCP Port: ${RUNPOD_TCP_PORT_8000:-'Não mapeada'}"

        # Salvar URLs em arquivo para fácil acesso
        cat > "$WORKSPACE_DIR/runpod_urls.txt" << EOF
# RunPod URLs - Arsenal de Guerra
PROXY_URL=https://${RUNPOD_POD_ID}-8000.proxy.runpod.net
PUBLIC_IP=${RUNPOD_PUBLIC_IP:-}
TCP_PORT=${RUNPOD_TCP_PORT_8000:-}

# Para Continue VSCode, use:
# "apiBase": "https://${RUNPOD_POD_ID}-8000.proxy.runpod.net/v1"
EOF

        echo "💾 URLs salvas em: $WORKSPACE_DIR/runpod_urls.txt"
    fi
}

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

echo "🔥 ARSENAL DE GUERRA - DEEPSEEK-CODER-V2.5"
echo "============================================="
echo "🎯 Modo: $([ "$RUNPOD_MODE" = true ] && echo "RunPod Pod" || echo "Local")"
echo "📦 Modelo: $MODEL_ID"
echo "🌐 Porta: $PORT"
echo "💾 Cache: $HF_HOME"
echo "🧠 Context: ${MAX_MODEL_LEN} tokens"
echo "👨‍💻 Autor: FULANOKS*CODER"
echo "============================================="

# Executar verificações
detect_gpu
check_dependencies
setup_runpod_urls

# ============================================================================
# CONSTRUÇÃO DO COMANDO vLLM OTIMIZADO
# ============================================================================

CMD=(
    python -m vllm.entrypoints.api_server
    --model "$MODEL_ID"
    --host 0.0.0.0
    --port "$PORT"
    --max-model-len "$MAX_MODEL_LEN"
    --dtype auto
    --gpu-memory-utilization "$GPU_UTIL"
    --tensor-parallel-size "$TENSOR_PARALLEL"
    --trust-remote-code
    --disable-log-stats
    --served-model-name "deepseek-coder"
)

# Adicionar configurações específicas do RunPod
if [ "$RUNPOD_MODE" = true ]; then
    CMD+=(
        --max-num-batched-tokens 8192
        --max-num-seqs 256
        --enable-prefix-caching
    )
else
    CMD+=(
        --max-num-batched-tokens 4096
        --max-num-seqs 128
    )
fi

# ============================================================================
# HEALTH CHECK E MONITORAMENTO
# ============================================================================

# Função para health check
health_check() {
    local max_attempts=30
    local attempt=1

    echo "🏥 Aguardando servidor ficar pronto..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
            echo "✅ Servidor pronto! (tentativa $attempt/$max_attempts)"

            # Testar endpoint de modelos
            if curl -s "http://localhost:$PORT/v1/models" >/dev/null 2>&1; then
                echo "✅ API funcionando corretamente!"

                if [ "$RUNPOD_MODE" = true ]; then
                    echo ""
                    echo "🎯 CONTINUE VSCODE - CONFIGURAÇÃO:"
                    echo "\"apiBase\": \"https://${RUNPOD_POD_ID}-8000.proxy.runpod.net/v1\""
                    echo ""
                fi

                return 0
            fi
        fi

        echo "⏳ Tentativa $attempt/$max_attempts - aguardando..."
        sleep 10
        ((attempt++))
    done

    echo "❌ Servidor não respondeu após $max_attempts tentativas"
    return 1
}

# ============================================================================
# INICIALIZAÇÃO FINAL
# ============================================================================

echo ""
echo "🚀 Iniciando DeepSeek-Coder-V2.5..."
echo "📝 Comando: ${CMD[*]}"
echo ""

# Executar health check em background
(
    sleep 30  # Aguardar um pouco antes de começar o health check
    health_check
) &

# Executar vLLM como processo principal
exec "${CMD[@]}"