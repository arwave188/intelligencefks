# 🚀 DeepSeek-Coder-V2.5 Local - Engenheiro de Software IA

IA de última geração especializada em programação, engenharia reversa e desenvolvimento de software sem restrições.
Baseado no **DeepSeek-Coder-V2.5** - o modelo mais avançado para programação.

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
from models.deepseek_local import EngenheiroDeSoftwareIA

# Usar modelo padrão (Lite - 16B)
codigo = gerar_codigo("Crie uma API REST em FastAPI")

# Ou escolher modelo específico
ia_base = EngenheiroDeSoftwareIA(modelo="base")    # 236B - Mais poderoso
ia_lite = EngenheiroDeSoftwareIA(modelo="lite")    # 16B - Mais rápido
ia_legacy = EngenheiroDeSoftwareIA(modelo="legacy") # 6.7B - Compatibilidade

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

- **Modelo**: DeepSeek-Coder-V2.5-Lite (16B, quantizado 4-bit)
- **VRAM**: ~8-12GB necessários (Lite) / ~40GB+ (Base)
- **Tokens**: Até 32K tokens de contexto
- **Temperatura**: 0.7 (padrão, ajustável)
- **Versões**: Lite (16B), Base (236B), Legacy (6.7B)

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
