"""
Servidor FastAPI para execução remota do agente AI-Dev.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from .routes.tasks import router as tasks_router
from .routes.health import router as health_router

# Configurar logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(
    title="AI-Dev API",
    description="API para execução remota do agente AI-Dev",
    version="1.0.0"
)

# Configurar CORS para operação sem censura
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(health_router, prefix="/health", tags=["health"])

# Estado global para tarefas em execução
running_tasks: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação."""
    logger.info("AI-Dev API iniciando...")

    # Configurações para operação sem censura
    uncensored_mode = os.getenv("UNCENSORED_MODE", "false").lower() == "true"
    if uncensored_mode:
        logger.info("🔓 Modo sem censura ativado - Todas as restrições de conteúdo desabilitadas")
        os.environ["DISABLE_CONTENT_FILTER"] = "true"
        os.environ["ALLOW_UNSAFE_CODE"] = "true"
        os.environ["BYPASS_SAFETY_CHECKS"] = "true"

    # Criar diretórios necessários
    runs_dir = Path(".runs")
    runs_dir.mkdir(exist_ok=True)

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Verificar se está rodando no RunPod
    runpod_mode = os.getenv("RUNPOD_MODE", "false").lower() == "true"
    if runpod_mode:
        logger.info("🚀 Executando no RunPod")
        pod_id = os.getenv("RUNPOD_POD_ID", "unknown")
        logger.info(f"Pod ID: {pod_id}")

    logger.info("AI-Dev API iniciada com sucesso!")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza na finalização."""
    logger.info("AI-Dev API finalizando...")
    
    # Cancelar tarefas em execução
    for task_id, task_info in running_tasks.items():
        if "task" in task_info and not task_info["task"].done():
            task_info["task"].cancel()
            logger.info(f"Tarefa {task_id} cancelada")


@app.get("/")
async def root():
    """Endpoint raiz."""
    uncensored_mode = os.getenv("UNCENSORED_MODE", "false").lower() == "true"
    runpod_mode = os.getenv("RUNPOD_MODE", "false").lower() == "true"

    return {
        "message": "AI-Dev API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "uncensored_mode": uncensored_mode,
        "runpod_mode": runpod_mode,
        "ssl_enabled": True,
        "https_port": 8443,
        "features": [
            "Uncensored AI Development",
            "HTTPS/SSL Support",
            "RunPod Optimized",
            "No Content Filtering",
            "Full API Access"
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "api.server:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
