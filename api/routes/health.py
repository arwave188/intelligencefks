"""
Rotas de health check e status do sistema.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str
    timestamp: str
    version: str
    services: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check básico."""
    services = {}
    
    # Verificar LLM backend
    llm_backend = os.getenv("LLM_BACKEND", "openai")
    services["llm"] = {
        "backend": llm_backend,
        "status": "unknown"
    }
    
    try:
        # Teste básico do LLM
        from models.llm_client import get_llm_client
        client = get_llm_client()
        services["llm"]["status"] = "ok"
    except Exception as e:
        services["llm"]["status"] = "error"
        services["llm"]["error"] = str(e)
    
    # Verificar banco de vetores
    vector_backend = os.getenv("VECTOR_BACKEND", "qdrant")
    services["vector_db"] = {
        "backend": vector_backend,
        "status": "unknown"
    }
    
    try:
        if vector_backend == "qdrant":
            from qdrant_client import QdrantClient
            
            qdrant_url = os.getenv("QDRANT_URL")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            
            if qdrant_url and qdrant_api_key:
                client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            else:
                host = os.getenv("QDRANT_HOST", "localhost")
                port = int(os.getenv("QDRANT_PORT", "6333"))
                client = QdrantClient(host=host, port=port)
            
            # Teste de conexão
            collections = client.get_collections()
            services["vector_db"]["status"] = "ok"
            services["vector_db"]["collections"] = len(collections.collections)
            
        elif vector_backend == "pinecone":
            from pinecone import Pinecone
            
            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("PINECONE_API_KEY não configurada")
            
            client = Pinecone(api_key=api_key)
            indexes = client.list_indexes()
            services["vector_db"]["status"] = "ok"
            services["vector_db"]["indexes"] = len(indexes)
            
    except Exception as e:
        services["vector_db"]["status"] = "error"
        services["vector_db"]["error"] = str(e)
    
    # Status geral
    overall_status = "ok"
    for service in services.values():
        if service["status"] == "error":
            overall_status = "degraded"
            break
        elif service["status"] == "unknown":
            overall_status = "unknown"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        services=services
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check para Kubernetes."""
    try:
        # Verificações básicas
        health = await health_check()
        
        if health.status in ["ok", "degraded"]:
            return {"status": "ready"}
        else:
            return {"status": "not_ready"}, 503
            
    except Exception as e:
        logger.error(f"Readiness check falhou: {e}")
        return {"status": "not_ready", "error": str(e)}, 503


@router.get("/live")
async def liveness_check():
    """Liveness check para Kubernetes."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
