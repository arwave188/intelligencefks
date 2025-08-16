"""
Recuperador de contexto com estratégias de diversidade.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from rich.console import Console

# Imports opcionais para Pinecone
try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """Chunk recuperado com metadados."""
    text: str
    path: str
    symbol: str
    lang: str
    score: float
    start_line: int
    end_line: int
    chunk_type: str


@dataclass
class ContextPack:
    """Pacote de contexto pronto para injeção no prompt."""
    chunks: List[RetrievedChunk]
    summary: str
    total_tokens: int
    files_included: List[str]


class CodeRetriever:
    """Recuperador de código com estratégias de diversidade."""

    def __init__(self):
        # Configuração do backend de vetores
        self.vector_backend = os.getenv("VECTOR_BACKEND", "qdrant")

        # Configurações Qdrant
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_code = os.getenv("QDRANT_COLLECTION_CODE", "code_chunks")
        self.collection_summaries = os.getenv("QDRANT_COLLECTION_SUMMARIES", "summaries")

        # Configurações Pinecone
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_index = os.getenv("PINECONE_INDEX", "ai-dev-code")

        # Parâmetros de recuperação
        self.top_k = int(os.getenv("RAG_TOPK", "8"))
        self.max_per_file = int(os.getenv("RAG_MAX_PER_FILE", "3"))
        self.min_similarity = float(os.getenv("RAG_MIN_SIMILARITY", "0.7"))

        # Inicializar cliente de vetores
        self.vector_client = None
        self.pinecone_index_client = None
        self._init_vector_client()

        # Inicializar modelo de embeddings
        embedding_model = os.getenv("EMBEDDING_MODEL", "jinaai/jina-embeddings-v3")
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
        except Exception:
            console.print(f"[yellow]Modelo {embedding_model} não encontrado, usando alternativo[/yellow]")
            self.embedding_model = SentenceTransformer("intfloat/e5-base-v2")

    def _init_vector_client(self):
        """Inicializa cliente do banco de vetores."""
        if self.vector_backend == "qdrant":
            if self.qdrant_url and self.qdrant_api_key:
                self.vector_client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key
                )
            else:
                self.vector_client = QdrantClient(
                    host=self.qdrant_host,
                    port=self.qdrant_port
                )

        elif self.vector_backend == "pinecone":
            if not PINECONE_AVAILABLE:
                raise ImportError("Pinecone não disponível")

            if not self.pinecone_api_key:
                raise ValueError("PINECONE_API_KEY não configurada")

            pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            self.pinecone_index_client = pinecone_client.Index(self.pinecone_index)
    
    def search_code(
        self,
        query: str,
        repo_path: Optional[str] = None,
        language: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """
        Busca chunks de código por similaridade.
        
        Args:
            query: Consulta de busca
            repo_path: Filtrar por repositório específico
            language: Filtrar por linguagem
            top_k: Número máximo de resultados
        
        Returns:
            Lista de chunks recuperados
        """
        if top_k is None:
            top_k = self.top_k
        
        try:
            # Gerar embedding da consulta
            query_embedding = self.embedding_model.encode(query).tolist()

            # Buscar baseado no backend
            if self.vector_backend == "qdrant":
                chunks = self._search_qdrant(query_embedding, repo_path, language, top_k)
            elif self.vector_backend == "pinecone":
                chunks = self._search_pinecone(query_embedding, repo_path, language, top_k)
            else:
                raise ValueError(f"Backend não suportado: {self.vector_backend}")

            # Aplicar estratégia de diversidade
            diverse_chunks = self._apply_diversity_strategy(chunks, top_k)

            logger.info(f"Recuperados {len(diverse_chunks)} chunks para query: {query[:50]}...")

            return diverse_chunks

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []

    def _search_qdrant(self, query_embedding: List[float], repo_path: Optional[str],
                      language: Optional[str], top_k: int) -> List[RetrievedChunk]:
        """Busca no Qdrant."""
        # Construir filtros
        filters = []
        if repo_path:
            filters.append(FieldCondition(key="path", match=MatchValue(value=repo_path)))
        if language:
            filters.append(FieldCondition(key="lang", match=MatchValue(value=language)))

        filter_condition = Filter(must=filters) if filters else None

        # Buscar
        search_result = self.vector_client.search(
            collection_name=self.collection_code,
            query_vector=query_embedding,
            query_filter=filter_condition,
            limit=top_k * 2,
            score_threshold=self.min_similarity
        )

        # Converter para RetrievedChunk
        chunks = []
        for point in search_result:
            payload = point.payload
            chunk = RetrievedChunk(
                text=payload["text"],
                path=payload["path"],
                symbol=payload["symbol"],
                lang=payload["lang"],
                score=point.score,
                start_line=payload.get("start_line", 0),
                end_line=payload.get("end_line", 0),
                chunk_type=payload.get("type", "unknown")
            )
            chunks.append(chunk)

        return chunks

    def _search_pinecone(self, query_embedding: List[float], repo_path: Optional[str],
                        language: Optional[str], top_k: int) -> List[RetrievedChunk]:
        """Busca no Pinecone."""
        # Construir filtros
        filter_dict = {"collection_type": "code"}
        if repo_path:
            filter_dict["path"] = repo_path
        if language:
            filter_dict["lang"] = language

        # Buscar
        search_result = self.pinecone_index_client.query(
            vector=query_embedding,
            filter=filter_dict,
            top_k=top_k * 2,
            include_metadata=True
        )

        # Converter para RetrievedChunk
        chunks = []
        for match in search_result.matches:
            if match.score < self.min_similarity:
                continue

            metadata = match.metadata
            chunk = RetrievedChunk(
                text=metadata["text"],
                path=metadata["path"],
                symbol=metadata["symbol"],
                lang=metadata["lang"],
                score=match.score,
                start_line=metadata.get("start_line", 0),
                end_line=metadata.get("end_line", 0),
                chunk_type=metadata.get("type", "unknown")
            )
            chunks.append(chunk)

        return chunks
    
    def _apply_diversity_strategy(self, chunks: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
        """Aplica estratégia de diversidade por arquivo e diretório."""
        if not chunks:
            return []
        
        # Agrupar por arquivo
        by_file = defaultdict(list)
        for chunk in chunks:
            by_file[chunk.path].append(chunk)
        
        # Selecionar chunks com diversidade
        selected = []
        file_counts = defaultdict(int)
        
        # Ordenar chunks por score
        sorted_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
        
        for chunk in sorted_chunks:
            if len(selected) >= top_k:
                break
            
            # Verificar limite por arquivo
            if file_counts[chunk.path] >= self.max_per_file:
                continue
            
            selected.append(chunk)
            file_counts[chunk.path] += 1
        
        return selected
    
    def search_summaries(self, query: str, summary_type: str = "file") -> List[Dict[str, Any]]:
        """Busca sumários de arquivos ou diretórios."""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Filtrar por tipo
            filter_condition = Filter(must=[
                FieldCondition(key="type", match=MatchValue(value=summary_type))
            ])
            
            search_result = self.qdrant.search(
                collection_name=self.collection_summaries,
                query_vector=query_embedding,
                query_filter=filter_condition,
                limit=5
            )
            
            summaries = []
            for point in search_result:
                summaries.append({
                    "path": point.payload["path"],
                    "summary": point.payload["summary"],
                    "score": point.score,
                    "type": point.payload["type"]
                })
            
            return summaries
            
        except Exception as e:
            logger.error(f"Erro na busca de sumários: {e}")
            return []
    
    def build_context_pack(
        self,
        query: str,
        repo_path: Optional[str] = None,
        max_tokens: int = 8000
    ) -> ContextPack:
        """
        Constrói pacote de contexto completo para o prompt.
        
        Args:
            query: Consulta/tarefa
            repo_path: Caminho do repositório
            max_tokens: Limite de tokens
        
        Returns:
            Pacote de contexto estruturado
        """
        # Buscar chunks de código
        code_chunks = self.search_code(query, repo_path)
        
        # Buscar sumários relevantes
        file_summaries = self.search_summaries(query, "file")
        dir_summaries = self.search_summaries(query, "directory")
        
        # Estimar tokens (aproximação: 1 token ≈ 4 caracteres)
        current_tokens = 0
        selected_chunks = []
        
        for chunk in code_chunks:
            chunk_tokens = len(chunk.text) // 4
            if current_tokens + chunk_tokens > max_tokens * 0.8:  # 80% para código
                break
            
            selected_chunks.append(chunk)
            current_tokens += chunk_tokens
        
        # Gerar sumário do contexto
        files_included = list(set(chunk.path for chunk in selected_chunks))
        
        summary_parts = [f"Contexto para: {query}"]
        summary_parts.append(f"Arquivos incluídos: {', '.join(files_included[:5])}")
        
        if file_summaries:
            summary_parts.append("Sumários relevantes:")
            for summary in file_summaries[:3]:
                summary_parts.append(f"- {summary['summary'][:100]}...")
        
        context_summary = "\n".join(summary_parts)
        
        return ContextPack(
            chunks=selected_chunks,
            summary=context_summary,
            total_tokens=current_tokens,
            files_included=files_included
        )
    
    def format_context_for_prompt(self, context_pack: ContextPack) -> str:
        """Formata contexto para injeção no prompt."""
        lines = [
            "=== CONTEXTO DO REPOSITÓRIO ===",
            "",
            context_pack.summary,
            "",
            "=== CÓDIGO RELEVANTE ===",
            ""
        ]
        
        for i, chunk in enumerate(context_pack.chunks, 1):
            lines.extend([
                f"## Chunk {i}: {chunk.path} - {chunk.symbol}",
                f"Linguagem: {chunk.lang} | Score: {chunk.score:.3f}",
                f"Linhas: {chunk.start_line}-{chunk.end_line}",
                "",
                "```" + chunk.lang,
                chunk.text,
                "```",
                ""
            ])
        
        lines.append("=== FIM DO CONTEXTO ===")
        
        return "\n".join(lines)


def retrieve_context(
    query: str,
    repo_path: Optional[str] = None,
    max_tokens: int = 8000
) -> str:
    """Função de conveniência para recuperar contexto formatado."""
    retriever = CodeRetriever()
    context_pack = retriever.build_context_pack(query, repo_path, max_tokens)
    return retriever.format_context_for_prompt(context_pack)
