#!/usr/bin/env python3
"""
🔥 ARSENAL DE GUERRA - SERVIDOR vLLM DEEPSEEK 70B
Servidor otimizado para RunPod A100 80GB VRAM / 117GB RAM
Autor: FULANOKS*CODER - Arsenal de Guerra Digital
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verificar dependências críticas
try:
    import torch
    import vllm
    from vllm import LLM, SamplingParams
    from vllm.entrypoints.api_server import run_server
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.engine.async_llm_engine import AsyncLLMEngine
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
    import uvicorn
    DEPENDENCIES_OK = True
except ImportError as e:
    logger.error(f"❌ Dependência faltando: {e}")
    DEPENDENCIES_OK = False

class DeepSeekArsenalServer:
    """Servidor vLLM otimizado para DeepSeek 70B no RunPod"""
    
    def __init__(self):
        self.app = FastAPI(
            title="🔥 Arsenal de Guerra - DeepSeek 70B",
            description="Servidor vLLM otimizado para RunPod A100",
            version="2.5.0"
        )
        
        # Configurações do ambiente
        self.setup_environment()
        
        # Configurações do modelo
        self.model_config = self.get_optimized_config()
        
        # Engine vLLM
        self.engine: Optional[AsyncLLMEngine] = None
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Registrar rotas
        self.setup_routes()
        
        logger.info("🔥 Arsenal de Guerra - DeepSeek 70B Server inicializado")
    
    def setup_environment(self):
        """Configura variáveis de ambiente otimizadas"""
        
        # Detectar se está no RunPod
        self.is_runpod = os.getenv("RUNPOD_POD_ID") is not None
        
        # Configurações CUDA otimizadas para B200 180GB - MÁXIMA PERFORMANCE! 🔥
        os.environ.update({
            "CUDA_VISIBLE_DEVICES": "0",
            "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:2048,expandable_segments:True,roundup_power2_divisions:16",
            "TOKENIZERS_PARALLELISM": "false",
            "VLLM_USE_MODELSCOPE": "false",
            "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
            "VLLM_ENGINE_ITERATION_TIMEOUT_S": "3600",  # Timeout maior para B200
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            # Otimizações específicas B200
            "VLLM_ATTENTION_BACKEND": "FLASHINFER",
            "VLLM_USE_TRITON_FLASH_ATTN": "true",
            "VLLM_FLASH_ATTN_CHUNK_SIZE": "1",
            "VLLM_ENABLE_CUDA_GRAPH": "true",
            "VLLM_CUDA_GRAPH_MAX_SEQ_LEN": "8192",
            "CUDA_LAUNCH_BLOCKING": "0",
            "CUDA_CACHE_DISABLE": "0",
            "CUDA_DEVICE_MAX_CONNECTIONS": "32"
        })
        
        # Cache otimizado
        if self.is_runpod:
            cache_dir = "/workspace/cache"
        else:
            cache_dir = os.path.expanduser("~/.cache")
            
        os.environ.update({
            "HF_HOME": f"{cache_dir}/huggingface",
            "TRANSFORMERS_CACHE": f"{cache_dir}/transformers",
            "HF_DATASETS_CACHE": f"{cache_dir}/datasets"
        })
        
        # Criar diretórios de cache
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(f"{cache_dir}/huggingface").mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🏗️ Ambiente configurado - RunPod: {self.is_runpod}")
        logger.info(f"💾 Cache: {cache_dir}")
    
    def get_optimized_config(self) -> Dict[str, Any]:
        """Configurações otimizadas para B200 180GB VRAM - PERFORMANCE SUPREMA"""

        # Detectar GPU
        gpu_memory = 0
        gpu_name = "Unknown"
        if torch.cuda.is_available():
            gpu_props = torch.cuda.get_device_properties(0)
            gpu_memory = gpu_props.total_memory / (1024**3)
            gpu_name = gpu_props.name

        logger.info(f"🎮 GPU detectada: {gpu_name} ({gpu_memory:.1f}GB VRAM)")

        # Configurações baseadas na GPU - OTIMIZADO PARA B200!
        if gpu_memory >= 170:  # B200 180GB - CONFIGURAÇÃO SUPREMA! 🔥
            config = {
                "model": "deepseek-ai/DeepSeek-Coder-V2.5-Instruct",
                "tensor_parallel_size": 1,
                "gpu_memory_utilization": 0.98,  # MÁXIMO para B200!
                "max_model_len": 65536,  # CONTEXT MÁXIMO! 64K tokens
                "max_num_batched_tokens": 32768,  # BATCH GIGANTE!
                "max_num_seqs": 1024,  # SEQUÊNCIAS MASSIVAS!
                "enable_prefix_caching": True,
                "use_v2_block_manager": True,
                "swap_space": 0,  # SEM SWAP - TUDO NA GPU!
                "cpu_offload_gb": 0,  # ZERO CPU OFFLOAD!
                "block_size": 32,  # BLOCOS OTIMIZADOS
                "max_paddings": 512,
                "enable_chunked_prefill": True,
                "max_num_on_the_fly_seq_groups": 1024,
                "enable_cuda_graph": True,
                "cuda_graph_max_seq_len": 8192
            }
            logger.info("🔥🔥🔥 CONFIGURAÇÃO B200 SUPREMA ATIVADA! 🔥🔥🔥")

        elif gpu_memory >= 75:  # A100 80GB
            config = {
                "model": "deepseek-ai/DeepSeek-Coder-V2.5-Instruct",
                "tensor_parallel_size": 1,
                "gpu_memory_utilization": 0.95,
                "max_model_len": 32768,
                "max_num_batched_tokens": 8192,
                "max_num_seqs": 256,
                "enable_prefix_caching": True,
                "use_v2_block_manager": True,
                "swap_space": 4,
                "cpu_offload_gb": 0
            }
        elif gpu_memory >= 40:  # A100 40GB
            config = {
                "model": "deepseek-ai/DeepSeek-Coder-V2.5-Instruct",
                "tensor_parallel_size": 1,
                "gpu_memory_utilization": 0.90,
                "max_model_len": 16384,
                "max_num_batched_tokens": 4096,
                "max_num_seqs": 128,
                "enable_prefix_caching": True,
                "use_v2_block_manager": True,
                "swap_space": 8,
                "cpu_offload_gb": 10
            }
        else:  # Outras GPUs - usar modelo menor
            config = {
                "model": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
                "tensor_parallel_size": 1,
                "gpu_memory_utilization": 0.85,
                "max_model_len": 8192,
                "max_num_batched_tokens": 2048,
                "max_num_seqs": 64,
                "enable_prefix_caching": False,
                "use_v2_block_manager": False,
                "swap_space": 16,
                "cpu_offload_gb": 20
            }
        
        # Configurações comuns
        config.update({
            "host": "0.0.0.0",
            "port": 8000,
            "dtype": "auto",
            "trust_remote_code": True,
            "disable_log_stats": True,
            "served_model_name": "deepseek-coder",
            "disable_log_requests": False,
            "max_log_len": 100
        })
        
        logger.info(f"⚙️ Configuração: {config['model']}")
        logger.info(f"🧠 Context: {config['max_model_len']} tokens")
        logger.info(f"💾 GPU Util: {config['gpu_memory_utilization']*100}%")
        
        return config
    
    async def initialize_engine(self):
        """Inicializa o engine vLLM"""
        if self.engine is not None:
            return
            
        logger.info("🚀 Inicializando vLLM Engine...")
        
        try:
            # Criar argumentos do engine
            engine_args = AsyncEngineArgs(
                model=self.model_config["model"],
                tensor_parallel_size=self.model_config["tensor_parallel_size"],
                gpu_memory_utilization=self.model_config["gpu_memory_utilization"],
                max_model_len=self.model_config["max_model_len"],
                max_num_batched_tokens=self.model_config["max_num_batched_tokens"],
                max_num_seqs=self.model_config["max_num_seqs"],
                enable_prefix_caching=self.model_config["enable_prefix_caching"],
                use_v2_block_manager=self.model_config["use_v2_block_manager"],
                swap_space=self.model_config["swap_space"],
                cpu_offload_gb=self.model_config["cpu_offload_gb"],
                dtype=self.model_config["dtype"],
                trust_remote_code=self.model_config["trust_remote_code"],
                disable_log_stats=self.model_config["disable_log_stats"],
                served_model_name=self.model_config["served_model_name"],
                disable_log_requests=self.model_config["disable_log_requests"],
                max_log_len=self.model_config["max_log_len"]
            )
            
            # Criar engine
            self.engine = AsyncLLMEngine.from_engine_args(engine_args)
            
            logger.info("✅ vLLM Engine inicializado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar engine: {e}")
            raise
    
    def setup_routes(self):
        """Configura as rotas da API"""
        
        @self.app.on_event("startup")
        async def startup_event():
            await self.initialize_engine()
        
        @self.app.get("/")
        async def root():
            return {
                "message": "🔥 Arsenal de Guerra - DeepSeek 70B",
                "status": "running",
                "model": self.model_config["model"],
                "version": "2.5.0"
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "deepseek-arsenal",
                "model": self.model_config["model"],
                "gpu_memory": f"{torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f}GB" if torch.cuda.is_available() else "N/A"
            }
        
        @self.app.get("/v1/models")
        async def list_models():
            return {
                "object": "list",
                "data": [
                    {
                        "id": "deepseek-coder",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "arsenal-de-guerra",
                        "permission": [],
                        "root": "deepseek-coder",
                        "parent": None
                    }
                ]
            }

        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: Request):
            """Endpoint compatível com OpenAI para Continue VSCode"""
            if self.engine is None:
                raise HTTPException(status_code=503, detail="Engine não inicializado")

            try:
                data = await request.json()

                # Extrair parâmetros
                messages = data.get("messages", [])
                model = data.get("model", "deepseek-coder")
                max_tokens = data.get("max_tokens", 2048)
                temperature = data.get("temperature", 0.8)
                top_p = data.get("top_p", 0.95)
                stream = data.get("stream", False)
                stop = data.get("stop", ["<|im_end|>", "</s>"])

                # Converter mensagens para prompt
                prompt = self.messages_to_prompt(messages)

                # Parâmetros de sampling
                sampling_params = SamplingParams(
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stop=stop,
                    skip_special_tokens=True
                )

                # Gerar resposta
                if stream:
                    return StreamingResponse(
                        self.stream_generate(prompt, sampling_params),
                        media_type="text/plain"
                    )
                else:
                    # Geração não-streaming
                    results = await self.engine.generate(prompt, sampling_params, request_id=f"req_{int(time.time())}")

                    if results:
                        output = results[0].outputs[0]
                        response_text = output.text

                        return {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "message": {
                                        "role": "assistant",
                                        "content": response_text
                                    },
                                    "finish_reason": "stop"
                                }
                            ],
                            "usage": {
                                "prompt_tokens": len(prompt.split()),
                                "completion_tokens": len(response_text.split()),
                                "total_tokens": len(prompt.split()) + len(response_text.split())
                            }
                        }
                    else:
                        raise HTTPException(status_code=500, detail="Falha na geração")

            except Exception as e:
                logger.error(f"❌ Erro em chat/completions: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/completions")
        async def completions(request: Request):
            """Endpoint de completions para compatibilidade"""
            if self.engine is None:
                raise HTTPException(status_code=503, detail="Engine não inicializado")

            try:
                data = await request.json()

                # Extrair parâmetros
                prompt = data.get("prompt", "")
                model = data.get("model", "deepseek-coder")
                max_tokens = data.get("max_tokens", 2048)
                temperature = data.get("temperature", 0.8)
                top_p = data.get("top_p", 0.95)
                stream = data.get("stream", False)
                stop = data.get("stop", ["<|im_end|>", "</s>"])

                # Parâmetros de sampling
                sampling_params = SamplingParams(
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stop=stop,
                    skip_special_tokens=True
                )

                # Gerar resposta
                results = await self.engine.generate(prompt, sampling_params, request_id=f"req_{int(time.time())}")

                if results:
                    output = results[0].outputs[0]
                    response_text = output.text

                    return {
                        "id": f"cmpl-{int(time.time())}",
                        "object": "text_completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "text": response_text,
                                "index": 0,
                                "logprobs": None,
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": len(prompt.split()),
                            "completion_tokens": len(response_text.split()),
                            "total_tokens": len(prompt.split()) + len(response_text.split())
                        }
                    }
                else:
                    raise HTTPException(status_code=500, detail="Falha na geração")

            except Exception as e:
                logger.error(f"❌ Erro em completions: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def messages_to_prompt(self, messages: list) -> str:
        """Converte mensagens do formato OpenAI para prompt DeepSeek"""
        prompt_parts = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")

        # Adicionar início da resposta do assistant
        prompt_parts.append("<|im_start|>assistant\n")

        return "\n".join(prompt_parts)

    async def stream_generate(self, prompt: str, sampling_params: SamplingParams):
        """Geração streaming para Continue VSCode"""
        try:
            request_id = f"req_{int(time.time())}"

            async for output in self.engine.generate(prompt, sampling_params, request_id):
                if output.outputs:
                    text = output.outputs[0].text

                    # Formato SSE para streaming
                    chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": "deepseek-coder",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": text},
                                "finish_reason": None
                            }
                        ]
                    }

                    yield f"data: {json.dumps(chunk)}\n\n"

            # Chunk final
            final_chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "deepseek-coder",
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }

            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"❌ Erro no streaming: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

if __name__ == "__main__":
    if not DEPENDENCIES_OK:
        logger.error("❌ Instale as dependências: pip install vllm torch fastapi uvicorn")
        sys.exit(1)
    
    # Argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Arsenal de Guerra - DeepSeek 70B Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host do servidor")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor")
    parser.add_argument("--workers", type=int, default=1, help="Número de workers")
    args = parser.parse_args()
    
    # Criar servidor
    server = DeepSeekArsenalServer()
    
    # Executar servidor
    logger.info(f"🚀 Iniciando servidor em {args.host}:{args.port}")
    uvicorn.run(
        server.app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info",
        access_log=True
    )
