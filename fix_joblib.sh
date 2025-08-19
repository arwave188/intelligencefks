#!/usr/bin/env bash
# ============================================================================
# 🔥 ARSENAL DE GUERRA - CORREÇÃO RÁPIDA JOBLIB
# Corrige erro "No module named 'joblib'"
# Autor: FULANOKS*CODER - Arsenal de Guerra Digital
# ============================================================================

echo "🔥 ARSENAL DE GUERRA - CORREÇÃO RÁPIDA JOBLIB"
echo "=============================================="

# Instalar joblib e dependências faltantes
echo "📦 Instalando joblib e dependências..."
pip install joblib
pip install scikit-learn --upgrade
pip install threadpoolctl

# Verificar instalação
echo "🔍 Verificando instalação..."
python3 -c "
try:
    import joblib
    print('✅ joblib instalado com sucesso!')
    print(f'   Versão: {joblib.__version__}')
except ImportError as e:
    print(f'❌ Erro joblib: {e}')

try:
    import sklearn
    print('✅ scikit-learn funcionando!')
    print(f'   Versão: {sklearn.__version__}')
except ImportError as e:
    print(f'❌ Erro sklearn: {e}')

try:
    from transformers import AutoTokenizer
    print('✅ AutoTokenizer funcionando!')
except ImportError as e:
    print(f'❌ Erro AutoTokenizer: {e}')
"

# Tentar baixar modelo novamente
echo "📥 Tentando baixar modelo DeepSeek novamente..."
python3 -c "
try:
    from transformers import AutoTokenizer
    from huggingface_hub import snapshot_download
    import os
    
    cache_dir = '/workspace/cache/huggingface' if os.path.exists('/workspace') else os.path.expanduser('~/.cache/huggingface')
    
    print('🚀 Baixando tokenizer...')
    tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-Coder-V2.5-Instruct', cache_dir=cache_dir)
    print('✅ Tokenizer baixado com sucesso!')
    
    print('🚀 Baixando modelo...')
    snapshot_download('deepseek-ai/DeepSeek-Coder-V2.5-Instruct', cache_dir=cache_dir, ignore_patterns=['*.bin'])
    print('✅ Modelo baixado com sucesso!')
    
except Exception as e:
    print(f'❌ Erro no download: {e}')
    print('💡 Tente executar: pip install transformers --upgrade')
"

echo "✅ Correção concluída!"
echo "🚀 Agora execute: ./start_arsenal.sh"
