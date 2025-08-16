"""
RAG Persistente com Qdrant - Memória de longo prazo para DeepSeek
Indexa códigos, documentação e conhecimento para consulta rápida
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)

class RAGPersistente:
    """
    Sistema RAG persistente para DeepSeek-Coder-V2.5
    Mantém memória de códigos, documentação e conhecimento
    """
    
    def __init__(self, qdrant_url: str = "localhost:6333"):
        self.qdrant_url = qdrant_url
        self.collection_name = "deepseek_knowledge"
        self.embedding_model_name = "all-MiniLM-L6-v2"
        
        self.client = None
        self.embedding_model = None
        
        if not QDRANT_AVAILABLE:
            logger.warning("⚠️ Qdrant não disponível. Execute: pip install qdrant-client sentence-transformers")
            return
        
        self._inicializar_rag()
    
    def _inicializar_rag(self):
        """Inicializa cliente Qdrant e modelo de embeddings."""
        try:
            # Cliente Qdrant
            self.client = QdrantClient(url=self.qdrant_url)
            logger.info(f"✅ Conectado ao Qdrant: {self.qdrant_url}")
            
            # Modelo de embeddings
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"✅ Modelo de embeddings carregado: {self.embedding_model_name}")
            
            # Criar coleção se não existir
            self._criar_colecao()
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar RAG: {e}")
            self.client = None
            self.embedding_model = None
    
    def _criar_colecao(self):
        """Cria coleção no Qdrant se não existir."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # Dimensão do all-MiniLM-L6-v2
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Coleção '{self.collection_name}' criada")
            else:
                logger.info(f"✅ Coleção '{self.collection_name}' já existe")
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar coleção: {e}")
    
    def adicionar_codigo(
        self, 
        codigo: str, 
        linguagem: str, 
        descricao: str = "",
        tags: List[str] = None,
        arquivo: str = ""
    ) -> bool:
        """Adiciona código ao índice RAG."""
        if not self.client or not self.embedding_model:
            logger.warning("⚠️ RAG não inicializado")
            return False
        
        try:
            # Gerar embedding
            texto_completo = f"{descricao}\n\nCódigo ({linguagem}):\n{codigo}"
            embedding = self.embedding_model.encode(texto_completo).tolist()
            
            # Gerar ID único
            codigo_hash = hashlib.md5(codigo.encode()).hexdigest()
            
            # Metadados
            payload = {
                "codigo": codigo,
                "linguagem": linguagem,
                "descricao": descricao,
                "tags": tags or [],
                "arquivo": arquivo,
                "tipo": "codigo",
                "hash": codigo_hash
            }
            
            # Inserir no Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=codigo_hash,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"✅ Código adicionado ao RAG: {arquivo or 'sem_nome'}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar código: {e}")
            return False
    
    def adicionar_documentacao(
        self, 
        titulo: str, 
        conteudo: str, 
        categoria: str = "docs",
        tags: List[str] = None
    ) -> bool:
        """Adiciona documentação ao índice RAG."""
        if not self.client or not self.embedding_model:
            return False
        
        try:
            texto_completo = f"{titulo}\n\n{conteudo}"
            embedding = self.embedding_model.encode(texto_completo).tolist()
            
            doc_hash = hashlib.md5(texto_completo.encode()).hexdigest()
            
            payload = {
                "titulo": titulo,
                "conteudo": conteudo,
                "categoria": categoria,
                "tags": tags or [],
                "tipo": "documentacao",
                "hash": doc_hash
            }
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=doc_hash,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"✅ Documentação adicionada: {titulo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar documentação: {e}")
            return False
    
    def buscar_conhecimento(
        self, 
        query: str, 
        limite: int = 5,
        filtro_tipo: Optional[str] = None,
        filtro_linguagem: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca conhecimento relevante no RAG."""
        if not self.client or not self.embedding_model:
            return []
        
        try:
            # Gerar embedding da query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Construir filtros
            filtros = {}
            if filtro_tipo:
                filtros["tipo"] = filtro_tipo
            if filtro_linguagem:
                filtros["linguagem"] = filtro_linguagem
            
            # Buscar no Qdrant
            resultados = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limite,
                query_filter=filtros if filtros else None
            )
            
            # Processar resultados
            conhecimentos = []
            for resultado in resultados:
                conhecimento = {
                    "score": resultado.score,
                    "payload": resultado.payload,
                    "relevancia": "ALTA" if resultado.score > 0.8 else "MEDIA" if resultado.score > 0.6 else "BAIXA"
                }
                conhecimentos.append(conhecimento)
            
            logger.info(f"🔍 Encontrados {len(conhecimentos)} resultados para: {query[:50]}...")
            return conhecimentos
            
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return []
    
    def indexar_diretorio_codigo(self, caminho: str, extensoes: List[str] = None) -> int:
        """Indexa todos os códigos de um diretório."""
        if extensoes is None:
            extensoes = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php']
        
        caminho_obj = Path(caminho)
        if not caminho_obj.exists():
            logger.error(f"❌ Diretório não encontrado: {caminho}")
            return 0
        
        arquivos_indexados = 0
        
        for arquivo in caminho_obj.rglob("*"):
            if arquivo.is_file() and arquivo.suffix in extensoes:
                try:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        codigo = f.read()
                    
                    linguagem = self._detectar_linguagem(arquivo.suffix)
                    descricao = f"Arquivo: {arquivo.name}"
                    
                    if self.adicionar_codigo(
                        codigo=codigo,
                        linguagem=linguagem,
                        descricao=descricao,
                        arquivo=str(arquivo)
                    ):
                        arquivos_indexados += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao indexar {arquivo}: {e}")
        
        logger.info(f"✅ Indexados {arquivos_indexados} arquivos de código")
        return arquivos_indexados
    
    def _detectar_linguagem(self, extensao: str) -> str:
        """Detecta linguagem pela extensão do arquivo."""
        mapeamento = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        return mapeamento.get(extensao.lower(), 'unknown')
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas do RAG."""
        if not self.client:
            return {"erro": "RAG não inicializado"}
        
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "total_documentos": info.points_count,
                "status": info.status,
                "configuracao": {
                    "dimensao_vetores": info.config.params.vectors.size,
                    "distancia": info.config.params.vectors.distance,
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {"erro": str(e)}
    
    def limpar_colecao(self) -> bool:
        """Limpa toda a coleção (cuidado!)."""
        if not self.client:
            return False
        
        try:
            self.client.delete_collection(self.collection_name)
            self._criar_colecao()
            logger.info("🗑️ Coleção limpa e recriada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar coleção: {e}")
            return False

# Instância global
rag_persistente = RAGPersistente()

def adicionar_codigo_ao_rag(codigo: str, linguagem: str, descricao: str = "") -> bool:
    """Função de conveniência para adicionar código."""
    return rag_persistente.adicionar_codigo(codigo, linguagem, descricao)

def buscar_codigo_similar(query: str, linguagem: str = None) -> List[Dict]:
    """Função de conveniência para buscar código."""
    return rag_persistente.buscar_conhecimento(
        query=query,
        filtro_tipo="codigo",
        filtro_linguagem=linguagem
    )

def indexar_projeto(caminho: str) -> int:
    """Função de conveniência para indexar projeto."""
    return rag_persistente.indexar_diretorio_codigo(caminho)
