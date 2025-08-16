"""
Cliente LLM com suporte para APIs online e modelos locais.
"""
import json
import logging
import os
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio

import httpx
from rich.console import Console

# Imports opcionais para modelos locais
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    temperature: float = 0.2
    max_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 50


class LLMClient:
    """Cliente unificado para LLM com suporte a APIs online e modelos locais."""

    def __init__(self):
        self.backend = os.getenv("LLM_BACKEND", "openai")
        self.model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

        # Configurações de API
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        self.fireworks_api_key = os.getenv("FIREWORKS_API_KEY")
        self.deepinfra_api_key = os.getenv("DEEPINFRA_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Para modelos locais
        self.tokenizer = None
        self.model = None
        self.use_transformers = os.getenv("USE_TRANSFORMERS", "false").lower() == "true"

        # Cliente HTTP para APIs
        self.http_client = httpx.Client(timeout=300.0)

        # Inicializar modelo local se necessário
        if self.backend == "transformers" or self.use_transformers:
            if TRANSFORMERS_AVAILABLE:
                self._load_transformers_model()
            else:
                console.print("[red]Transformers não disponível. Instale com: pip install transformers torch[/red]")
                raise ImportError("Transformers não disponível")
    
    def _load_transformers_model(self):
        """Carrega modelo via Transformers com quantização 4-bit."""
        try:
            # Configuração de quantização 4-bit
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )

            # Modelo padrão se não especificado
            model_path = self.model_name
            if ":" in model_path:  # Formato Ollama
                model_path = "Qwen/Qwen2.5-Coder-7B-Instruct"

            console.print(f"[blue]Carregando modelo: {model_path}[/blue]")

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                padding_side="left"
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.bfloat16
            )

            # Adicionar pad token se não existir
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            console.print("[green]Modelo carregado com sucesso![/green]")

        except Exception as e:
            logger.error(f"Erro ao carregar modelo Transformers: {e}")
            console.print(f"[red]Erro ao carregar modelo: {e}[/red]")
            raise

    def _generate_with_openai_compatible(self, messages: List[Dict[str, str]], config: GenerationConfig) -> str:
        """Gera resposta usando API compatível com OpenAI."""
        try:
            # Determinar URL e chave baseado no backend
            if self.backend == "openai":
                base_url = self.openai_base_url
                api_key = self.openai_api_key
                model = self.model_name or "gpt-4o-mini"
            elif self.backend == "together":
                base_url = "https://api.together.xyz/v1"
                api_key = self.together_api_key
                model = self.model_name or "meta-llama/Llama-3.2-3B-Instruct-Turbo"
            elif self.backend == "fireworks":
                base_url = "https://api.fireworks.ai/inference/v1"
                api_key = self.fireworks_api_key
                model = self.model_name or "accounts/fireworks/models/llama-v3p1-8b-instruct"
            elif self.backend == "deepinfra":
                base_url = "https://api.deepinfra.com/v1/openai"
                api_key = self.deepinfra_api_key
                model = self.model_name or "meta-llama/Meta-Llama-3.1-8B-Instruct"
            else:
                raise ValueError(f"Backend {self.backend} não suportado para OpenAI-compatible")

            if not api_key:
                raise ValueError(f"API key não configurada para {self.backend}")

            # Preparar payload
            payload = {
                "model": model,
                "messages": messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "top_p": config.top_p
            }

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            logger.info(f"Chamando {self.backend} API: {model}")

            response = self.http_client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers
            )

            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            logger.info(f"Resposta gerada: {len(content)} caracteres")

            return content

        except Exception as e:
            logger.error(f"Erro na API {self.backend}: {e}")
            raise

    def _generate_with_anthropic(self, messages: List[Dict[str, str]], config: GenerationConfig) -> str:
        """Gera resposta usando API da Anthropic."""
        try:
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY não configurada")

            # Separar system message
            system_message = ""
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)

            # Preparar payload
            payload = {
                "model": self.model_name or "claude-3-5-sonnet-20241022",
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "messages": user_messages
            }

            if system_message:
                payload["system"] = system_message

            headers = {
                "x-api-key": self.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }

            logger.info(f"Chamando Anthropic API: {payload['model']}")

            response = self.http_client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers
            )

            response.raise_for_status()
            result = response.json()

            content = result["content"][0]["text"]
            logger.info(f"Resposta gerada: {len(content)} caracteres")

            return content

        except Exception as e:
            logger.error(f"Erro na API Anthropic: {e}")
            raise
    
    def _generate_with_ollama(self, messages: List[Dict[str, str]], config: GenerationConfig) -> str:
        """Gera resposta usando Ollama (local ou remoto)."""
        try:
            # Tentar API REST primeiro (se OLLAMA_BASE_URL configurado)
            if self.ollama_base_url and self.ollama_base_url != "http://localhost:11434":
                return self._generate_with_ollama_api(messages, config)

            # Fallback para CLI local
            prompt = self._messages_to_prompt(messages)

            cmd = [
                "ollama", "generate",
                self.model_name,
                "--prompt", prompt,
                "--temperature", str(config.temperature),
                "--num-predict", str(config.max_tokens)
            ]

            logger.info(f"Executando Ollama CLI: {' '.join(cmd[:3])}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise RuntimeError(f"Ollama falhou: {result.stderr}")

            response = result.stdout.strip()
            logger.info(f"Resposta gerada: {len(response)} caracteres")

            return response

        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout na geração com Ollama")
        except Exception as e:
            logger.error(f"Erro no Ollama: {e}")
            raise

    def _generate_with_ollama_api(self, messages: List[Dict[str, str]], config: GenerationConfig) -> str:
        """Gera resposta usando API REST do Ollama."""
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k
                }
            }

            logger.info(f"Chamando Ollama API: {self.ollama_base_url}")

            response = self.http_client.post(
                f"{self.ollama_base_url}/api/chat",
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            content = result["message"]["content"]
            logger.info(f"Resposta gerada: {len(content)} caracteres")

            return content

        except Exception as e:
            logger.error(f"Erro na API Ollama: {e}")
            raise
    
    def _generate_with_transformers(self, messages: List[Dict[str, str]], config: GenerationConfig) -> str:
        """Gera resposta usando Transformers."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Modelo Transformers não carregado")
        
        try:
            # Converter mensagens para prompt
            prompt = self._messages_to_prompt(messages)
            
            # Tokenizar
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096 - config.max_tokens
            )
            
            # Mover para GPU se disponível
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Gerar
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    top_k=config.top_k,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decodificar apenas a parte nova
            input_length = inputs["input_ids"].shape[1]
            generated_tokens = outputs[0][input_length:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            logger.info(f"Resposta gerada: {len(response)} caracteres")
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Erro no Transformers: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Converte lista de mensagens para prompt."""
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")
        
        prompt_parts.append("<|im_start|>assistant\n")
        
        return "\n".join(prompt_parts)
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
        system: Optional[str] = None
    ) -> str:
        """
        Gera resposta do LLM.

        Args:
            messages: Lista de mensagens [{"role": "user", "content": "..."}]
            temperature: Temperatura de geração
            max_tokens: Máximo de tokens
            system: Prompt de sistema (opcional)

        Returns:
            Resposta gerada
        """
        # Adicionar sistema se fornecido
        if system:
            messages = [{"role": "system", "content": system}] + messages

        config = GenerationConfig(
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Log do prompt (truncado)
        prompt_preview = str(messages)[:200] if messages else ""
        logger.info(f"Backend: {self.backend}, Prompt: {prompt_preview}...")

        # Gerar resposta baseado no backend
        try:
            if self.backend == "anthropic":
                response = self._generate_with_anthropic(messages, config)
            elif self.backend in ["openai", "together", "fireworks", "deepinfra"]:
                response = self._generate_with_openai_compatible(messages, config)
            elif self.backend == "ollama":
                response = self._generate_with_ollama(messages, config)
            elif self.backend == "transformers" or self.use_transformers:
                response = self._generate_with_transformers(messages, config)
            else:
                raise ValueError(f"Backend não suportado: {self.backend}")

            # Log da resposta
            logger.info(f"Resposta: {len(response)} caracteres")

            return response

        except Exception as e:
            logger.error(f"Erro na geração com {self.backend}: {e}")
            raise

    def __del__(self):
        """Cleanup do cliente HTTP."""
        if hasattr(self, 'http_client'):
            try:
                self.http_client.close()
            except Exception:
                pass


# Instância global
_client = None


def get_llm_client() -> LLMClient:
    """Retorna instância singleton do cliente LLM."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def generate(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 2048,
    system: Optional[str] = None
) -> str:
    """Função de conveniência para geração."""
    client = get_llm_client()
    return client.generate(messages, temperature, max_tokens, system)
