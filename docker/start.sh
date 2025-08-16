#!/bin/bash
# Script de inicialização automática para RunPod
# Inicia DeepSeek-Coder-V2.5 + vLLM + RAG automaticamente

set -e

echo "🚀 Iniciando DeepSeek-Coder-V2.5 + vLLM + RAG..."
echo "📦 Modelo: $MODEL_NAME"
echo "🌐 Porta: $VLLM_PORT"

# Função para log com timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Verificar GPU
log "🔍 Verificando GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    log "✅ $GPU_COUNT GPU(s) detectada(s)"
else
    log "⚠️ GPU não detectada, usando CPU"
fi

# Verificar espaço em disco
log "💾 Verificando espaço em disco..."
df -h /app

# Criar diretórios necessários
log "📁 Criando diretórios..."
mkdir -p /app/models /app/data /app/logs /app/cache

# Configurar cache do Hugging Face
export HF_HOME=/app/cache
export TRANSFORMERS_CACHE=/app/cache
export HF_DATASETS_CACHE=/app/cache

# Função para iniciar Qdrant (RAG)
start_qdrant() {
    log "🗄️ Iniciando Qdrant para RAG..."
    
    # Verificar se Qdrant está instalado
    if command -v qdrant &> /dev/null; then
        qdrant --config-path /app/rag/qdrant_config.yaml &
        QDRANT_PID=$!
        log "✅ Qdrant iniciado (PID: $QDRANT_PID)"
    else
        log "⚠️ Qdrant não encontrado, RAG será limitado"
    fi
}

# Função para verificar se o modelo está disponível
check_model() {
    log "🔍 Verificando modelo $MODEL_NAME..."
    
    python3 -c "
import torch
from transformers import AutoTokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained('$MODEL_NAME', trust_remote_code=True)
    print('✅ Modelo acessível')
except Exception as e:
    print(f'❌ Erro ao acessar modelo: {e}')
    exit(1)
"
}

# Função para iniciar servidor vLLM
start_vllm_server() {
    log "🚀 Iniciando servidor vLLM..."
    
    # Verificar se vLLM está disponível
    if python3 -c "import vllm" 2>/dev/null; then
        log "✅ vLLM disponível"
        
        # Iniciar servidor customizado
        python3 /app/server/vllm_server.py &
        VLLM_PID=$!
        log "✅ Servidor vLLM iniciado (PID: $VLLM_PID)"
        
        # Aguardar servidor ficar pronto
        log "⏳ Aguardando servidor ficar pronto..."
        for i in {1..60}; do
            if curl -s http://localhost:$VLLM_PORT/health > /dev/null; then
                log "✅ Servidor vLLM pronto!"
                break
            fi
            sleep 5
            log "⏳ Tentativa $i/60..."
        done
        
    else
        log "❌ vLLM não disponível, usando fallback"
        # Fallback para servidor simples
        python3 -c "
from models.deepseek_local import engenheiro_ia
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'healthy', 'model': 'deepseek-fallback'}

@app.post('/v1/chat/completions')
def chat(request: dict):
    prompt = request.get('messages', [{}])[-1].get('content', '')
    response = engenheiro_ia.gerar_codigo_avancado(prompt)
    return {
        'choices': [{'message': {'content': response}}]
    }

uvicorn.run(app, host='0.0.0.0', port=$VLLM_PORT)
" &
        FALLBACK_PID=$!
        log "✅ Servidor fallback iniciado (PID: $FALLBACK_PID)"
    fi
}

# Função para mostrar informações de conexão
show_connection_info() {
    log "📋 Informações de Conexão:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 Endpoint vLLM: http://0.0.0.0:$VLLM_PORT"
    echo "📝 Chat Completions: http://0.0.0.0:$VLLM_PORT/v1/chat/completions"
    echo "❤️ Health Check: http://0.0.0.0:$VLLM_PORT/health"
    echo "📚 Modelos: http://0.0.0.0:$VLLM_PORT/v1/models"
    echo ""
    echo "🔗 Para Continue VSCode:"
    echo "   - URL: http://localhost:$VLLM_PORT"
    echo "   - Modelo: deepseek-coder"
    echo "   - API: OpenAI Compatible"
    echo ""
    echo "🗄️ RAG Qdrant: http://0.0.0.0:6333"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Função para monitorar processos
monitor_processes() {
    log "👁️ Monitorando processos..."
    
    while true; do
        # Verificar se vLLM ainda está rodando
        if ! curl -s http://localhost:$VLLM_PORT/health > /dev/null; then
            log "❌ Servidor vLLM não responde, reiniciando..."
            start_vllm_server
        fi
        
        sleep 30
    done
}

# Função de limpeza ao sair
cleanup() {
    log "🧹 Limpando processos..."
    if [ ! -z "$VLLM_PID" ]; then
        kill $VLLM_PID 2>/dev/null || true
    fi
    if [ ! -z "$QDRANT_PID" ]; then
        kill $QDRANT_PID 2>/dev/null || true
    fi
    if [ ! -z "$FALLBACK_PID" ]; then
        kill $FALLBACK_PID 2>/dev/null || true
    fi
    log "👋 Shutdown completo"
}

# Configurar trap para limpeza
trap cleanup EXIT INT TERM

# Executar inicialização
main() {
    log "🎯 Iniciando sequência de boot..."
    
    # 1. Verificar modelo
    check_model
    
    # 2. Iniciar RAG (opcional)
    # start_qdrant
    
    # 3. Iniciar servidor vLLM
    start_vllm_server
    
    # 4. Mostrar informações
    show_connection_info
    
    # 5. Monitorar (loop infinito)
    monitor_processes
}

# Executar função principal
main
