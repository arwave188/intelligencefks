# AI-Dev: IA Engenheira de Software

Uma IA engenheira de software completa que pode ler, entender e modificar repositórios de código de forma autônoma.

## Características

- 🔍 **RAG Avançado**: Indexação com AST + embeddings para compreensão profunda do código
- 🛠️ **Correção Autônoma**: Corrige bugs e implementa funcionalidades automaticamente
- 🔄 **Ciclo Iterativo**: Planeja → Recupera contexto → Gera patch → Aplica → Testa → Itera
- 🎯 **Treinável**: Suporte para SFT (LoRA/QLoRA) + DPO/ORPO
- 🐳 **Sandbox Seguro**: Execução isolada em Docker com limites de recursos
- 📊 **Observabilidade**: Logs estruturados e trilhas de execução

## Requisitos

- Python 3.11+
- Docker e Docker Compose
- 8GB+ RAM (recomendado para modelos locais)

## Instalação Rápida

1. **Clone e configure o ambiente:**
```bash
git clone <repo-url>
cd ai-dev
cp .env.example .env
```

2. **Opção A - Local:**
```bash
make setup
source .venv/bin/activate
```

3. **Opção B - Docker:**
```bash
make compose-up
docker compose run --rm app bash
```

4. **Inicie o Qdrant:**
```bash
make compose-up
```

## Uso Básico

### 1. Indexar um repositório
```bash
python -m scripts.index_repo --repo examples/repo_teste --rebuild
```

### 2. Executar o agente
```bash
python cli.py fix "Corrigir soma errada" --repo examples/repo_teste
```

### 3. Ver resultados
Os artefatos ficam salvos em `.runs/<timestamp>/`

## Comandos Disponíveis

```bash
# CLI Principal
python cli.py plan "<tarefa>"                    # Apenas planejar
python cli.py fix "<tarefa>" --repo <path>       # Corrigir bug
python cli.py implement "<tarefa>" --repo <path> # Implementar funcionalidade
python cli.py index --repo <path>                # Indexar repositório
python cli.py api --host 0.0.0.0 --port 8000    # Iniciar API
python cli.py status                             # Status do sistema

# Treinamento
python cli.py train sft --train data/sft_train.jsonl --eval data/sft_eval.jsonl
python cli.py train dpo --data data/dpo_train.jsonl

# Via Makefile
make index REPO=examples/repo_teste
make agent TASK="Corrigir soma" REPO=examples/repo_teste
make api                                         # Iniciar API
make api-dev                                     # API com auto-reload
make compose-up-api                              # Docker com API
make test
make train-sft
```

## Configuração

Edite o arquivo `.env` para ajustar:

### Backends LLM
- **LLM_BACKEND**: `openai`, `anthropic`, `together`, `fireworks`, `deepinfra`, `ollama`, `transformers`
- **LLM_MODEL**: Modelo a usar (ex: `gpt-4o-mini`, `claude-3-5-sonnet-20241022`)
- **API Keys**: Configure as chaves apropriadas (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)

### Bancos de Vetores
- **VECTOR_BACKEND**: `qdrant` ou `pinecone`
- **Qdrant Cloud**: `QDRANT_URL` e `QDRANT_API_KEY`
- **Pinecone**: `PINECONE_API_KEY`, `PINECONE_ENV`, `PINECONE_INDEX`

### Outros
- **RAG_TOPK**: Número de chunks recuperados
- **MAX_ITERS**: Máximo de iterações do agente

## Exemplo Funcional

O projeto inclui um exemplo em `examples/repo_teste/` com um bug proposital:

```python
# utils.py - BUG: retorna subtração em vez de soma
def add(a, b):
    return a - b  # Deveria ser a + b
```

Execute o agente para corrigir automaticamente:
```bash
bash scripts/run_agent_example.sh
```

## Arquitetura

```
ai-dev/
├── agent/           # Core do agente
│   ├── planner.py   # Loop principal
│   ├── tools.py     # Ferramentas (linters, testes)
│   ├── editor.py    # Aplicação de patches
│   ├── sandbox.py   # Execução isolada
│   └── memory/      # Sistema RAG
├── models/          # Cliente LLM
├── training/        # Fine-tuning
├── eval/           # Avaliação
└── configs/        # Configurações YAML
```

## Deploy Cloud

### Railway

1. **Conectar repositório ao Railway**
2. **Configurar variáveis de ambiente:**
   - `LLM_BACKEND=openai`
   - `OPENAI_API_KEY=sua_chave`
   - `VECTOR_BACKEND=qdrant`
   - `QDRANT_URL=sua_url_qdrant_cloud`
   - `QDRANT_API_KEY=sua_chave_qdrant`
3. **Deploy automático via Git push**

### Render

1. **Conectar repositório GitHub ao Render**
2. **Usar arquivo `cloud/deploy_render.yaml`**
3. **Configurar Secrets no dashboard:**
   - API keys do LLM
   - Credenciais do banco de vetores
4. **Deploy automático**

### HuggingFace Spaces

1. **Criar Space (tipo Docker)**
2. **Copiar arquivos para repositório do Space**
3. **Configurar Secrets:**
   ```
   OPENAI_API_KEY=sua_chave
   QDRANT_URL=sua_url
   QDRANT_API_KEY=sua_chave
   ```
4. **Push para deploy**

## API Web

O projeto inclui uma API FastAPI para execução remota:

```bash
# Iniciar API localmente
python cli.py api --port 8000

# Ou via Docker
make compose-up-api
```

### Endpoints principais:
- `POST /tasks/run` - Executar tarefa
- `GET /tasks/{id}/logs` - Stream de logs
- `GET /health` - Health check

### Exemplo de uso:
```bash
# Executar tarefa
curl -X POST http://localhost:8000/tasks/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Corrigir soma errada",
    "repo_url": "https://github.com/user/repo.git",
    "max_iters": 5
  }'

# Acompanhar logs
curl -N http://localhost:8000/tasks/{task_id}/logs
```

## Treinamento

### 1. Gerar dataset sintético
```bash
python training/sft_dataset.py --n 1000 --langs py,ts
```

### 2. Fine-tuning SFT
```bash
python training/finetune_lora.py --train data/sft_train.jsonl --eval data/sft_eval.jsonl
```

### 3. Treinamento DPO
```bash
python training/dpo_train.py --data data/dpo_train.jsonl
```

## Troubleshooting

### Qdrant não conecta
```bash
docker compose logs qdrant
# Verifique se a porta 6333 está livre
```

### Modelo não carrega
```bash
# Para Ollama
ollama pull Qwen2.5-Coder:14b

# Para Transformers, verifique RAM disponível
```

### Sandbox falha
```bash
# Verifique se Docker está rodando
docker ps
```

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request
