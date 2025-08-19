#!/usr/bin/env bash
# ============================================================================
# 🔥 ARSENAL DE GUERRA - INSTALAÇÃO COM CORREÇÃO DE DEPENDÊNCIAS
# Script alternativo para resolver conflitos de dependências
# Autor: FULANOKS*CODER - Arsenal de Guerra Digital
# ============================================================================

set -euo pipefail

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# Banner
echo -e "${RED}"
echo "============================================================================"
echo "🔥🔥🔥 ARSENAL DE GUERRA - CORREÇÃO DE DEPENDÊNCIAS B200 🔥🔥🔥"
echo "============================================================================"
echo "🎯 RESOLVENDO CONFLITOS DE DEPENDÊNCIAS"
echo "⚡ INSTALAÇÃO ROBUSTA PARA B200 180GB"
echo "🚀 AUTOR: FULANOKS*CODER - Arsenal de Guerra Digital"
echo "============================================================================"
echo -e "${NC}"

# Detectar ambiente
if [[ -n "${RUNPOD_POD_ID:-}" ]]; then
    export IS_RUNPOD=true
    export WORKSPACE_DIR="/workspace"
    export CACHE_DIR="/workspace/cache"
    log "✅ RunPod detectado - ID: ${RUNPOD_POD_ID}"
else
    export IS_RUNPOD=false
    export WORKSPACE_DIR="$(pwd)"
    export CACHE_DIR="$HOME/.cache"
    warning "⚠️ Ambiente local detectado"
fi

# Detectar GPU
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
    GPU_NAME=$(echo "$GPU_INFO" | cut -d',' -f1 | xargs)
    GPU_MEMORY=$(echo "$GPU_INFO" | cut -d',' -f2 | xargs)
    
    log "🎮 GPU detectada: $GPU_NAME ($GPU_MEMORY MB VRAM)"
    
    if [[ $GPU_MEMORY -ge 170000 ]]; then
        export GPU_TIER="B200_180GB"
        log "🔥🔥🔥 B200 180GB DETECTADA - CONFIGURAÇÃO SUPREMA! 🔥🔥🔥"
    elif [[ $GPU_MEMORY -ge 75000 ]]; then
        export GPU_TIER="A100_80GB"
        log "🚀 A100 80GB detectada"
    else
        export GPU_TIER="OTHER"
        warning "⚠️ GPU com VRAM limitada"
    fi
else
    error "❌ NVIDIA GPU não detectada!"
    exit 1
fi

# Configurar ambiente
log "🏗️ Configurando ambiente..."
mkdir -p "$CACHE_DIR"/{huggingface,transformers,datasets,pip}
mkdir -p "$WORKSPACE_DIR"/{logs,data,models}

# Configurar variáveis de ambiente
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:2048,expandable_segments:True"
export TOKENIZERS_PARALLELISM=false
export HF_HOME="$CACHE_DIR/huggingface"
export TRANSFORMERS_CACHE="$CACHE_DIR/transformers"
export HF_DATASETS_CACHE="$CACHE_DIR/datasets"
export PIP_CACHE_DIR="$CACHE_DIR/pip"
export HF_HUB_ENABLE_HF_TRANSFER=1

# Atualizar sistema
log "🔧 Atualizando sistema..."
python3 -m pip install --upgrade pip setuptools wheel

# Limpar cache pip se necessário
log "🧹 Limpando cache pip..."
python3 -m pip cache purge

# Instalação por etapas para evitar conflitos
log "📦 Instalação por etapas para evitar conflitos..."

# Etapa 1: PyTorch (base)
info "🔥 Etapa 1: Instalando PyTorch para CUDA 12.x..."
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall

# Etapa 2: Transformers ecosystem
info "🤖 Etapa 2: Instalando Transformers ecosystem..."
python3 -m pip install transformers tokenizers accelerate huggingface-hub safetensors

# Etapa 3: vLLM (crítico)
info "⚡ Etapa 3: Instalando vLLM..."
python3 -m pip install vllm

# Etapa 4: Web server
info "🌐 Etapa 4: Instalando servidor web..."
python3 -m pip install fastapi "uvicorn[standard]" httpx sse-starlette python-multipart websockets

# Etapa 5: ML e utilities
info "📊 Etapa 5: Instalando ML e utilities..."
python3 -m pip install numpy scipy pydantic python-dotenv requests rich tqdm psutil

# Etapa 6: Datasets e embeddings
info "📚 Etapa 6: Instalando datasets e embeddings..."
python3 -m pip install datasets sentence-transformers

# Etapa 7: Otimizações opcionais
info "🚀 Etapa 7: Tentando instalar otimizações (opcional)..."
python3 -m pip install flash-attn --no-build-isolation || warning "⚠️ Flash Attention não instalado (opcional)"
python3 -m pip install xformers || warning "⚠️ xFormers não instalado (opcional)"
python3 -m pip install bitsandbytes || warning "⚠️ BitsAndBytes não instalado (opcional)"

# Verificar instalação
log "🔍 Verificando instalação..."
python3 -c "
import torch
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ CUDA disponível: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
    print(f'✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f}GB')

try:
    import vllm
    print(f'✅ vLLM: {vllm.__version__}')
except:
    print('❌ vLLM não instalado')

try:
    import transformers
    print(f'✅ Transformers: {transformers.__version__}')
except:
    print('❌ Transformers não instalado')

try:
    import fastapi
    print(f'✅ FastAPI: {fastapi.__version__}')
except:
    print('❌ FastAPI não instalado')
"

# Criar configuração .env
log "⚙️ Criando configuração .env..."
cat > "$WORKSPACE_DIR/.env" << EOF
# Arsenal de Guerra - Configuração B200 180GB
IS_RUNPOD=$IS_RUNPOD
WORKSPACE_DIR=$WORKSPACE_DIR
CACHE_DIR=$CACHE_DIR
GPU_TIER=$GPU_TIER

# Modelo
OPTIMAL_MODEL=deepseek-ai/DeepSeek-Coder-V2.5-Instruct
MODEL_NAME=deepseek-ai/DeepSeek-Coder-V2.5-Instruct

# vLLM B200 Supremo
TENSOR_PARALLEL_SIZE=1
GPU_MEMORY_UTILIZATION=0.98
MAX_MODEL_LEN=65536
MAX_NUM_BATCHED_TOKENS=32768
MAX_NUM_SEQS=1024
ENABLE_PREFIX_CACHING=true
USE_V2_BLOCK_MANAGER=true
SWAP_SPACE=0
CPU_OFFLOAD_GB=0

# Servidor
HOST=0.0.0.0
PORT=8000
API_PORT=8080

# Arsenal
UNCENSORED_MODE=true
DISABLE_CONTENT_FILTER=true
ALLOW_UNSAFE_CODE=true
ARSENAL_VERSION=2.5.0

# RunPod (substitua pela sua ID real)
RUNPOD_POD_ID=SEU_RUNPOD_ID
EOF

# Baixar modelo
log "📥 Baixando modelo DeepSeek..."
python3 -c "
from transformers import AutoTokenizer
from huggingface_hub import snapshot_download
import os

print('🚀 Iniciando download do modelo...')
try:
    tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-Coder-V2.5-Instruct', cache_dir='$CACHE_DIR/huggingface')
    print('📝 Tokenizer baixado!')
    
    snapshot_download('deepseek-ai/DeepSeek-Coder-V2.5-Instruct', cache_dir='$CACHE_DIR/huggingface', ignore_patterns=['*.bin'])
    print('✅ Modelo baixado!')
except Exception as e:
    print(f'⚠️ Erro no download: {e}')
"

# Criar script de start
log "📝 Criando script de inicialização..."
cat > "$WORKSPACE_DIR/start_arsenal.sh" << 'EOF'
#!/bin/bash
source .env
echo "🔥🔥🔥 ARSENAL B200 180GB - INICIANDO! 🔥🔥🔥"

# Verificar GPU
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Iniciar vLLM
echo "🚀 Iniciando vLLM B200 SUPREMO..."
python3 server/vllm_server.py &
VLLM_PID=$!

# Aguardar vLLM
echo "⏳ Aguardando vLLM..."
for i in {1..120}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ vLLM B200 pronto!"
        break
    fi
    sleep 5
done

# Iniciar API
echo "🌐 Iniciando API..."
python3 api/main.py &

echo "🎯 ARSENAL B200 180GB OPERACIONAL!"
echo "📊 vLLM: http://localhost:8000"
echo "🌐 API: http://localhost:8080"
echo "💀 Execute no PC: python3 arsenal_auto.py"

wait
EOF

chmod +x "$WORKSPACE_DIR/start_arsenal.sh"

# Finalizar
echo -e "${GREEN}"
echo "============================================================================"
echo "🎉🎉🎉 ARSENAL B200 180GB INSTALADO COM CORREÇÃO! 🎉🎉🎉"
echo "============================================================================"
echo -e "${WHITE}"
echo "🚀 PRÓXIMOS PASSOS:"
echo "   1. ./start_arsenal.sh (iniciar servidores)"
echo "   2. NO PC: python3 arsenal_auto.py (configurar Continue)"
echo ""
echo "🎯 SERVIDORES:"
echo "   vLLM: http://localhost:8000"
echo "   API: http://localhost:8080"
echo ""
echo "🔥🔥🔥 ARSENAL B200 180GB PRONTO PARA GUERRA DIGITAL! 🔥🔥🔥"
echo "💀 FULANOKS*CODER - Arsenal de Guerra Digital"
echo -e "${NC}"
