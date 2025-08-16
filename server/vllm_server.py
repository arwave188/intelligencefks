#!/usr/bin/env python3
"""
Servidor vLLM automático para DeepSeek-Coder-V2.5
Compatível com Continue VSCode e OpenAI API
"""

import os
import sys
import asyncio
import logging
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verificar se vLLM está disponível
try:
    from vllm import LLM, SamplingParams
    from vllm.entrypoints.openai.api_server import app as vllm_app
    VLLM_AVAILABLE = True
    logger.info("✅ vLLM disponível")
except ImportError:
    VLLM_AVAILABLE = False
    logger.warning("⚠️ vLLM não encontrado, usando fallback")

class DeepSeekVLLMServer:
    """Servidor vLLM otimizado para DeepSeek-Coder-V2.5"""
    
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct")
        self.port = int(os.getenv("VLLM_PORT", "8000"))
        self.host = os.getenv("VLLM_HOST", "0.0.0.0")
        self.max_model_len = int(os.getenv("MAX_MODEL_LEN", "32768"))
        self.gpu_memory_utilization = float(os.getenv("GPU_MEMORY_UTIL", "0.9"))
        
        self.llm = None
        
        logger.info(f"🚀 Inicializando servidor vLLM")
        logger.info(f"📦 Modelo: {self.model_name}")
        logger.info(f"🌐 Endpoint: http://{self.host}:{self.port}")
    
    def inicializar_modelo(self):
        """Inicializa o modelo vLLM."""
        if not VLLM_AVAILABLE:
            raise ImportError("vLLM não está instalado. Execute: pip install vllm")
        
        try:
            logger.info("📥 Carregando modelo com vLLM...")
            
            self.llm = LLM(
                model=self.model_name,
                max_model_len=self.max_model_len,
                gpu_memory_utilization=self.gpu_memory_utilization,
                trust_remote_code=True,
                dtype="bfloat16",
                quantization="awq" if "awq" in self.model_name.lower() else None,
                tensor_parallel_size=torch.cuda.device_count() if torch.cuda.is_available() else 1,
                enforce_eager=False,
                disable_log_stats=False
            )
            
            logger.info("✅ Modelo carregado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def criar_app_fastapi(self):
        """Cria aplicação FastAPI compatível com Continue VSCode."""
        app = FastAPI(
            title="DeepSeek-Coder-V2.5 API",
            description="Servidor vLLM para DeepSeek-Coder-V2.5 - Compatível com Continue VSCode",
            version="1.0.0"
        )
        
        # CORS para VSCode
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Modelos de request/response
        class ChatMessage(BaseModel):
            role: str
            content: str
        
        class ChatRequest(BaseModel):
            model: str = "deepseek-coder"
            messages: list[ChatMessage]
            temperature: float = 0.7
            max_tokens: int = 2048
            stream: bool = False
        
        class ChatResponse(BaseModel):
            id: str
            object: str = "chat.completion"
            model: str
            choices: list
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "model": self.model_name,
                "vllm_available": VLLM_AVAILABLE,
                "gpu_available": torch.cuda.is_available(),
                "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
            }
        
        @app.get("/v1/models")
        async def list_models():
            """Lista modelos disponíveis (compatível com OpenAI API)."""
            return {
                "object": "list",
                "data": [
                    {
                        "id": "deepseek-coder",
                        "object": "model",
                        "created": 1677610602,
                        "owned_by": "deepseek-ai",
                        "permission": [],
                        "root": "deepseek-coder",
                        "parent": None,
                    }
                ]
            }
        
        @app.post("/v1/chat/completions")
        async def chat_completions(request: ChatRequest):
            """Endpoint de chat compatível com Continue VSCode."""
            if not self.llm:
                raise HTTPException(status_code=503, detail="Modelo não carregado")
            
            try:
                # Converter mensagens para prompt
                prompt = self._converter_mensagens_para_prompt(request.messages)
                
                # Configurar parâmetros de sampling
                sampling_params = SamplingParams(
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    stop=["<|im_end|>", "</s>"]
                )
                
                # Gerar resposta
                outputs = self.llm.generate([prompt], sampling_params)
                generated_text = outputs[0].outputs[0].text.strip()
                
                # Formato de resposta compatível com OpenAI
                response = {
                    "id": f"chatcmpl-{hash(prompt) % 1000000}",
                    "object": "chat.completion",
                    "created": 1677610602,
                    "model": "deepseek-coder",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": generated_text
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(generated_text.split()),
                        "total_tokens": len(prompt.split()) + len(generated_text.split())
                    }
                }
                
                return response
                
            except Exception as e:
                logger.error(f"❌ Erro na geração: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        return app
    
    def _converter_mensagens_para_prompt(self, messages: list) -> str:
        """Converte mensagens do formato OpenAI para formato DeepSeek."""
        prompt_parts = []
        
        for message in messages:
            role = message.role
            content = message.content
            
            if role == "system":
                prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")
        
        # Adicionar início da resposta do assistant
        prompt_parts.append("<|im_start|>assistant\n")
        
        return "\n".join(prompt_parts)
    
    async def iniciar_servidor(self):
        """Inicia o servidor vLLM."""
        logger.info("🚀 Iniciando servidor DeepSeek-Coder-V2.5...")
        
        # Carregar modelo
        if not self.inicializar_modelo():
            logger.error("❌ Falha ao carregar modelo")
            sys.exit(1)
        
        # Criar app FastAPI
        app = self.criar_app_fastapi()
        
        # Configurar uvicorn
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        
        logger.info(f"✅ Servidor rodando em http://{self.host}:{self.port}")
        logger.info("🔗 Continue VSCode pode se conectar agora!")
        logger.info("📝 Endpoint: /v1/chat/completions")
        
        await server.serve()

def main():
    """Função principal."""
    server = DeepSeekVLLMServer()
    
    try:
        asyncio.run(server.iniciar_servidor())
    except KeyboardInterrupt:
        logger.info("🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
