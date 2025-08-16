# 🚀 DeepSeek Local - Engenheiro de Software IA

IA especializada em programação, engenharia reversa e desenvolvimento de software sem restrições.

## ⚡ Instalação Rápida

```bash
# 1. Clone o repositório
git clone <seu-repo>
cd <seu-repo>

# 2. Instale dependências
pip install -r requirements.txt

# 3. Teste o funcionamento
python test_deepseek.py
```

## 🎯 Uso Básico

```python
from models.deepseek_local import gerar_codigo, revisar_codigo, criar_projeto

# Gerar código
codigo = gerar_codigo("Crie uma API REST em FastAPI")

# Revisar código existente
review = revisar_codigo(meu_codigo)

# Criar projeto completo
projeto = criar_projeto("Sistema de chat em tempo real", "Python")
```

## 🔧 RunPod.io Setup

1. **Criar Pod com GPU**:
   - Template: PyTorch 2.0+
   - GPU: RTX 4090 ou A100 (recomendado)
   - Storage: 50GB+

2. **Instalar no RunPod**:
```bash
git clone <seu-repo>
cd <seu-repo>
pip install -r requirements.txt
python test_deepseek.py
```

3. **Usar via Jupyter**:
```python
from models.deepseek_local import gerar_codigo
resultado = gerar_codigo("Seu prompt aqui")
print(resultado)
```

## 🎛️ Configurações

- **Modelo**: DeepSeek Coder 6.7B (quantizado 4-bit)
- **VRAM**: ~4-6GB necessários
- **Tokens**: Até 8192 tokens de contexto
- **Temperatura**: 0.7 (padrão, ajustável)

## 🔥 Funcionalidades

- ✅ **Geração de código** em qualquer linguagem
- ✅ **Revisão e otimização** de código existente  
- ✅ **Criação de projetos** completos do zero
- ✅ **Engenharia reversa** de sistemas
- ✅ **Sem censura** - IA totalmente livre
- ✅ **Otimizado para GPU** com quantização

## 📊 Performance

- **Velocidade**: ~20-50 tokens/segundo (RTX 4090)
- **Qualidade**: Especializado em programação
- **Memória**: Otimizado para GPUs de 8GB+

## 🚨 Troubleshooting

**Erro de CUDA**:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Erro de memória**:
- Reduza `max_tokens` para 1024 ou menos
- Use GPU com mais VRAM

**Modelo não carrega**:
- Verifique conexão com internet
- Aguarde download inicial (~3-5GB)

## 🎉 Pronto para Produção!

Este setup está otimizado para RunPod.io e pronto para uso profissional.
