# 🔥 ARSENAL DE GUERRA - RUNPOD POD GUIDE

## 🚀 **Deploy Automático no RunPod Pod**

### **📋 Pré-requisitos**
- Conta RunPod ativa
- GPU com pelo menos 24GB VRAM (recomendado: RTX 4090, A100)
- VSCode com extensão Continue instalada

---

## **🎯 PASSO 1: Criar Pod no RunPod**

### **1.1 Configuração do Pod**
```
Template: PyTorch 2.1
GPU: RTX 4090 (24GB) ou A100 (40GB+)
Container Disk: 50GB mínimo
Volume: 100GB (persistente)
Expose Ports: 8000
```

### **1.2 Configurações Avançadas**
```bash
# Environment Variables (opcional)
MODEL_ID=deepseek-ai/DeepSeek-Coder-V2-Instruct-70B
GPU_MEMORY_UTILIZATION=0.95
MAX_MODEL_LEN=32768
```

---

## **🎯 PASSO 2: Deploy Automático**

### **2.1 Conectar ao Pod**
```bash
# Via Web Terminal ou SSH
ssh root@SEU_POD_IP
```

### **2.2 Clone e Deploy**
```bash
# Ir para workspace persistente
cd /workspace

# Clonar projeto
git clone https://github.com/SEU_USUARIO/ai-dev.git
cd ai-dev

# Executar deploy automático
chmod +x docker/start.sh
./docker/start.sh
```

**🎉 PRONTO! O script faz tudo automaticamente:**
- ✅ Detecta GPU e otimiza configurações
- ✅ Instala dependências necessárias
- ✅ Baixa modelo DeepSeek automaticamente
- ✅ Inicia servidor vLLM otimizado
- ✅ Gera URLs de acesso
- ✅ Testa funcionamento

---

## **🎯 PASSO 3: Configurar Continue VSCode**

### **3.1 Obter URL do Pod**
Após o deploy, o script mostra:
```
🔗 CONFIGURANDO URLS RUNPOD:
📡 Proxy URL: https://abc123def-8000.proxy.runpod.net
```

### **3.2 Configurar Continue**
1. Copie `vscode/continue_config.json` para `~/.continue/config.json`
2. Substitua `SEU_RUNPOD_ID` pela ID real do seu pod
3. Exemplo: `https://abc123def-8000.proxy.runpod.net/v1`

### **3.3 Testar Continue**
1. Abra VSCode
2. `Ctrl+Shift+P` → "Continue: Open Chat"
3. Digite: "Olá, você está funcionando?"
4. Deve receber resposta do DeepSeek

---

## **🔧 COMANDOS ÚTEIS**

### **Verificar Status**
```bash
# Status do servidor
curl http://localhost:8000/health

# Listar modelos
curl http://localhost:8000/v1/models

# Ver processos
ps aux | grep vllm
```

### **Monitoramento**
```bash
# GPU usage
nvidia-smi
watch -n 1 nvidia-smi

# Logs
tail -f /var/log/syslog | grep vllm

# Espaço em disco
df -h
du -sh /workspace/cache
```

### **Reiniciar Servidor**
```bash
# Parar servidor
pkill -f vllm

# Reiniciar
cd /workspace/ai-dev
./docker/start.sh
```

---

## **⚡ OTIMIZAÇÕES AUTOMÁTICAS**

### **Detecção de GPU**
O script detecta automaticamente:
- **A100/H100**: Modelo FULL 70B, GPU util 95%
- **RTX 4090**: Modelo FULL 70B, GPU util 90%
- **RTX 3090**: Modelo LITE, GPU util 85%
- **Outras**: Configuração conservadora

### **Cache Inteligente**
```bash
# Cache persistente em /workspace
HF_HOME=/workspace/cache/huggingface
TRANSFORMERS_CACHE=/workspace/cache/transformers

# Sobrevive a reinicializações do pod
```

### **Performance Tuning**
```bash
# Configurações CUDA otimizadas
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Threading otimizado
OMP_NUM_THREADS=auto (baseado em CPU cores)

# vLLM otimizado para RunPod
--enable-prefix-caching
--max-num-batched-tokens 8192
```

---

## **🆘 SOLUÇÃO DE PROBLEMAS**

### **❌ "Out of Memory"**
```bash
# Reduzir utilização GPU
export GPU_MEMORY_UTILIZATION=0.8

# Usar modelo menor
export MODEL_ID=deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct

# Reiniciar
./docker/start.sh
```

### **❌ "Model Download Failed"**
```bash
# Verificar espaço em disco
df -h

# Limpar cache se necessário
rm -rf /workspace/cache/*

# Tentar novamente
./docker/start.sh
```

### **❌ "Continue não conecta"**
```bash
# Verificar URL
cat /workspace/runpod_urls.txt

# Testar API
curl https://SEU_POD_ID-8000.proxy.runpod.net/health

# Verificar configuração Continue
cat ~/.continue/config.json | grep apiBase
```

### **❌ "Pod muito lento"**
```bash
# Verificar se está usando GPU
nvidia-smi

# Verificar modelo carregado
curl http://localhost:8000/v1/models

# Verificar configurações
ps aux | grep vllm
```

---

## **💰 OTIMIZAÇÃO DE CUSTOS**

### **Auto-shutdown**
```bash
# Desligar automaticamente em 2 horas
echo "sudo shutdown -h now" | at now + 2 hours

# Cancelar auto-shutdown
atq  # ver jobs
atrm JOB_ID  # cancelar
```

### **Uso Eficiente**
```bash
# Ligar pod apenas quando desenvolver
# Usar Continue VSCode normalmente
# Desligar pod quando terminar

# Custo típico:
# RTX 4090: ~$1.50/hora
# A100: ~$3.00/hora
```

---

## **✅ CHECKLIST FINAL**

- [ ] Pod criado com GPU adequada
- [ ] Projeto clonado em `/workspace`
- [ ] Script `./docker/start.sh` executado
- [ ] Servidor respondendo em `/health`
- [ ] URL do proxy funcionando
- [ ] Continue VSCode configurado
- [ ] Teste de chat funcionando

---

## **🎯 PRÓXIMOS PASSOS**

1. **Desenvolvimento**: Use Continue VSCode normalmente
2. **Monitoramento**: Acompanhe uso de GPU/memória
3. **Backup**: Código fica em `/workspace` (persistente)
4. **Economia**: Desligue pod quando não usar

**🔥 Arsenal de Guerra pronto para ação! 🔥**
