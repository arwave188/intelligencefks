"""
Rotas para gerenciamento de tarefas do agente.
"""
import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Estado global para tarefas
running_tasks: Dict[str, Dict[str, Any]] = {}


class TaskRequest(BaseModel):
    """Requisição para executar tarefa."""
    task: str = Field(..., description="Descrição da tarefa")
    repo_url: Optional[str] = Field(None, description="URL do repositório Git")
    repo_zip: Optional[str] = Field(None, description="Base64 do ZIP do repositório")
    max_iters: int = Field(5, description="Máximo de iterações")
    dry_run: bool = Field(False, description="Apenas planejar, não executar")


class TaskResponse(BaseModel):
    """Resposta da criação de tarefa."""
    task_id: str
    status: str
    message: str
    logs_url: str


class TaskStatus(BaseModel):
    """Status de uma tarefa."""
    task_id: str
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    progress: Dict[str, Any]
    error: Optional[str]


@router.post("/run", response_model=TaskResponse)
async def run_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Executa uma tarefa do agente."""
    task_id = str(uuid.uuid4())
    
    # Validar entrada
    if not request.repo_url and not request.repo_zip:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer repo_url ou repo_zip"
        )
    
    # Criar diretório da tarefa
    task_dir = Path(f".runs/{task_id}")
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar metadados da tarefa
    task_metadata = {
        "task_id": task_id,
        "task": request.task,
        "repo_url": request.repo_url,
        "max_iters": request.max_iters,
        "dry_run": request.dry_run,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "progress": {},
        "error": None
    }
    
    with open(task_dir / "metadata.json", "w") as f:
        json.dump(task_metadata, f, indent=2)
    
    # Registrar tarefa
    running_tasks[task_id] = {
        "metadata": task_metadata,
        "task": None
    }
    
    # Executar em background
    background_tasks.add_task(execute_task, task_id, request)
    
    base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    
    return TaskResponse(
        task_id=task_id,
        status="queued",
        message="Tarefa criada e será executada em background",
        logs_url=f"{base_url}/tasks/{task_id}/logs"
    )


@router.get("/{task_id}/status", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Obtém status de uma tarefa."""
    task_dir = Path(f".runs/{task_id}")
    
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    # Carregar metadados
    metadata_file = task_dir / "metadata.json"
    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Metadados da tarefa não encontrados")
    
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    return TaskStatus(**metadata)


@router.get("/{task_id}/logs")
async def stream_task_logs(task_id: str):
    """Stream dos logs de uma tarefa em tempo real."""
    task_dir = Path(f".runs/{task_id}")
    
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    async def log_generator() -> AsyncGenerator[str, None]:
        log_file = task_dir / "agent.log"
        
        # Aguardar arquivo de log ser criado
        while not log_file.exists():
            await asyncio.sleep(0.5)
        
        # Stream do arquivo
        with open(log_file, "r") as f:
            # Enviar conteúdo existente
            content = f.read()
            if content:
                yield f"data: {json.dumps({'type': 'log', 'content': content})}\n\n"
            
            # Monitorar novas linhas
            while True:
                line = f.readline()
                if line:
                    yield f"data: {json.dumps({'type': 'log', 'content': line})}\n\n"
                else:
                    # Verificar se tarefa terminou
                    if task_id in running_tasks:
                        task_info = running_tasks[task_id]
                        if task_info.get("task") and task_info["task"].done():
                            # Enviar status final
                            metadata_file = task_dir / "metadata.json"
                            if metadata_file.exists():
                                with open(metadata_file) as mf:
                                    metadata = json.load(mf)
                                yield f"data: {json.dumps({'type': 'status', 'content': metadata})}\n\n"
                            break
                    
                    await asyncio.sleep(0.5)
    
    return EventSourceResponse(log_generator())


@router.get("/{task_id}/artifacts")
async def get_task_artifacts(task_id: str):
    """Lista artefatos gerados pela tarefa."""
    task_dir = Path(f".runs/{task_id}")
    
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    artifacts = []
    
    for file_path in task_dir.rglob("*"):
        if file_path.is_file() and file_path.name != "metadata.json":
            artifacts.append({
                "name": file_path.name,
                "path": str(file_path.relative_to(task_dir)),
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    
    return {"task_id": task_id, "artifacts": artifacts}


async def execute_task(task_id: str, request: TaskRequest):
    """Executa a tarefa em background."""
    task_dir = Path(f".runs/{task_id}")
    
    try:
        # Atualizar status
        await update_task_status(task_id, "running", started_at=datetime.utcnow().isoformat())
        
        # Preparar repositório
        repo_path = await prepare_repository(task_id, request)
        
        # Executar agente
        await run_agent(task_id, request.task, repo_path, request.max_iters, request.dry_run)
        
        # Sucesso
        await update_task_status(task_id, "completed", completed_at=datetime.utcnow().isoformat())
        
    except Exception as e:
        logger.error(f"Erro na tarefa {task_id}: {e}")
        await update_task_status(
            task_id, 
            "failed", 
            completed_at=datetime.utcnow().isoformat(),
            error=str(e)
        )
    
    finally:
        # Remover da lista de tarefas ativas
        if task_id in running_tasks:
            del running_tasks[task_id]


async def prepare_repository(task_id: str, request: TaskRequest) -> str:
    """Prepara o repositório para execução."""
    task_dir = Path(f".runs/{task_id}")
    repo_dir = task_dir / "repo"
    
    if request.repo_url:
        # Clonar repositório
        cmd = ["git", "clone", request.repo_url, str(repo_dir)]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Erro ao clonar repositório: {stderr.decode()}")
    
    elif request.repo_zip:
        # TODO: Implementar extração de ZIP
        raise NotImplementedError("Suporte a ZIP ainda não implementado")
    
    return str(repo_dir)


async def run_agent(task_id: str, task: str, repo_path: str, max_iters: int, dry_run: bool):
    """Executa o agente AI-Dev."""
    task_dir = Path(f".runs/{task_id}")
    log_file = task_dir / "agent.log"
    
    # Comando para executar o agente
    cmd = [
        "python", "cli.py", 
        "fix" if not dry_run else "plan",
        task,
        "--repo", repo_path,
        "--max-iters", str(max_iters)
    ]
    
    # Executar processo
    with open(log_file, "w") as f:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=f,
            stderr=asyncio.subprocess.STDOUT,
            cwd=Path.cwd()
        )
        
        await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Agente falhou com código {process.returncode}")


async def update_task_status(task_id: str, status: str, **kwargs):
    """Atualiza status da tarefa."""
    task_dir = Path(f".runs/{task_id}")
    metadata_file = task_dir / "metadata.json"
    
    # Carregar metadados existentes
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    # Atualizar
    metadata["status"] = status
    metadata.update(kwargs)
    
    # Salvar
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Atualizar cache
    if task_id in running_tasks:
        running_tasks[task_id]["metadata"] = metadata
