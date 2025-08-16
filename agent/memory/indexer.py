"""
Indexador de repositórios usando tree-sitter e embeddings.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import tree_sitter
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rich.console import Console
from rich.progress import track

# Imports opcionais para Pinecone
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    pinecone = None

console = Console()
logger = logging.getLogger(__name__)


class CodeIndexer:
    """Indexador de código com AST e embeddings."""

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
        self.pinecone_env = os.getenv("PINECONE_ENV", "us-east-1-aws")
        self.pinecone_index = os.getenv("PINECONE_INDEX", "ai-dev-code")

        # Inicializar cliente de vetores
        self.vector_client = None
        self.pinecone_client = None
        self._init_vector_client()

        # Inicializar modelo de embeddings
        embedding_model = os.getenv("EMBEDDING_MODEL", "jinaai/jina-embeddings-v3")
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
        except Exception:
            console.print(f"[yellow]Modelo {embedding_model} não encontrado, usando alternativo[/yellow]")
            self.embedding_model = SentenceTransformer("intfloat/e5-base-v2")

        # Inicializar parsers tree-sitter
        self.parsers = self._init_parsers()

        # Criar coleções/índices se não existirem
        self._ensure_collections()

    def _init_vector_client(self):
        """Inicializa cliente do banco de vetores."""
        if self.vector_backend == "qdrant":
            if self.qdrant_url and self.qdrant_api_key:
                # Qdrant Cloud
                self.vector_client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key
                )
                console.print("[green]Conectado ao Qdrant Cloud[/green]")
            else:
                # Qdrant local
                self.vector_client = QdrantClient(
                    host=self.qdrant_host,
                    port=self.qdrant_port
                )
                console.print("[green]Conectado ao Qdrant local[/green]")

        elif self.vector_backend == "pinecone":
            if not PINECONE_AVAILABLE:
                raise ImportError("Pinecone não disponível. Instale com: pip install pinecone-client")

            if not self.pinecone_api_key:
                raise ValueError("PINECONE_API_KEY não configurada")

            self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            console.print("[green]Conectado ao Pinecone[/green]")

        else:
            raise ValueError(f"Backend de vetores não suportado: {self.vector_backend}")
    
    def _init_parsers(self) -> Dict[str, Parser]:
        """Inicializa parsers tree-sitter para diferentes linguagens."""
        parsers = {}
        
        try:
            # Python
            PY_LANGUAGE = Language(tspython.language(), "python")
            py_parser = Parser()
            py_parser.set_language(PY_LANGUAGE)
            parsers["python"] = py_parser
            
            # JavaScript
            JS_LANGUAGE = Language(tsjavascript.language(), "javascript")
            js_parser = Parser()
            js_parser.set_language(JS_LANGUAGE)
            parsers["javascript"] = js_parser
            
            # TypeScript
            TS_LANGUAGE = Language(tstypescript.language(), "typescript")
            ts_parser = Parser()
            ts_parser.set_language(TS_LANGUAGE)
            parsers["typescript"] = ts_parser
            
            console.print("[green]Parsers tree-sitter inicializados[/green]")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar parsers: {e}")
            console.print(f"[red]Erro ao inicializar parsers: {e}[/red]")
        
        return parsers
    
    def _ensure_collections(self):
        """Garante que as coleções/índices existem."""
        try:
            vector_size = self.embedding_model.get_sentence_embedding_dimension()

            if self.vector_backend == "qdrant":
                self._ensure_qdrant_collections(vector_size)
            elif self.vector_backend == "pinecone":
                self._ensure_pinecone_indexes(vector_size)

        except Exception as e:
            logger.error(f"Erro ao criar coleções/índices: {e}")
            raise

    def _ensure_qdrant_collections(self, vector_size: int):
        """Cria coleções no Qdrant."""
        # Coleção de chunks de código
        if not self.vector_client.collection_exists(self.collection_code):
            self.vector_client.create_collection(
                collection_name=self.collection_code,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            console.print(f"[green]Coleção Qdrant {self.collection_code} criada[/green]")

        # Coleção de sumários
        if not self.vector_client.collection_exists(self.collection_summaries):
            self.vector_client.create_collection(
                collection_name=self.collection_summaries,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            console.print(f"[green]Coleção Qdrant {self.collection_summaries} criada[/green]")

    def _ensure_pinecone_indexes(self, vector_size: int):
        """Cria índices no Pinecone."""
        existing_indexes = [idx.name for idx in self.pinecone_client.list_indexes()]

        # Índice principal (combina código e sumários)
        if self.pinecone_index not in existing_indexes:
            self.pinecone_client.create_index(
                name=self.pinecone_index,
                dimension=vector_size,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.pinecone_env
                )
            )
            console.print(f"[green]Índice Pinecone {self.pinecone_index} criado[/green]")

        # Conectar ao índice
        self.pinecone_index_client = self.pinecone_client.Index(self.pinecone_index)

    def _upsert_vectors(self, points: List[PointStruct], collection_type: str):
        """Insere vetores no banco escolhido."""
        if self.vector_backend == "qdrant":
            collection_name = (
                self.collection_code if collection_type == "code"
                else self.collection_summaries
            )
            self.vector_client.upsert(
                collection_name=collection_name,
                points=points
            )

        elif self.vector_backend == "pinecone":
            # Converter PointStruct para formato Pinecone
            vectors = []
            for point in points:
                metadata = point.payload.copy()
                metadata["collection_type"] = collection_type

                vectors.append({
                    "id": str(point.id),
                    "values": point.vector,
                    "metadata": metadata
                })

            self.pinecone_index_client.upsert(vectors=vectors)
    
    def _get_language_from_extension(self, file_path: str) -> Optional[str]:
        """Determina a linguagem pelo arquivo."""
        ext = Path(file_path).suffix.lower()
        
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript"
        }
        
        return mapping.get(ext)
    
    def _extract_ast_nodes(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Extrai nós AST relevantes do código."""
        if language not in self.parsers:
            return []
        
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, "utf8"))
            
            nodes = []
            
            def traverse(node, depth=0):
                if depth > 10:  # Evitar recursão muito profunda
                    return
                
                # Tipos de nós que nos interessam
                relevant_types = {
                    "function_definition", "class_definition", "method_definition",
                    "function_declaration", "class_declaration", "method_declaration",
                    "arrow_function", "function_expression"
                }
                
                if node.type in relevant_types:
                    start_byte = node.start_byte
                    end_byte = node.end_byte
                    
                    # Extrair nome do símbolo
                    symbol_name = self._extract_symbol_name(node, code)
                    
                    nodes.append({
                        "type": node.type,
                        "symbol": symbol_name,
                        "start_byte": start_byte,
                        "end_byte": end_byte,
                        "start_point": node.start_point,
                        "end_point": node.end_point,
                        "text": code[start_byte:end_byte]
                    })
                
                # Continuar traversal
                for child in node.children:
                    traverse(child, depth + 1)
            
            traverse(tree.root_node)
            return nodes
            
        except Exception as e:
            logger.error(f"Erro ao extrair AST: {e}")
            return []
    
    def _extract_symbol_name(self, node, code: str) -> str:
        """Extrai o nome do símbolo de um nó AST."""
        try:
            # Procurar por nó de identificador
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte:child.end_byte]
            
            # Fallback: usar tipo do nó
            return f"<{node.type}>"
            
        except Exception:
            return f"<{node.type}>"
    
    def _chunk_by_blocks(self, code: str, max_size: int = 1000) -> List[Dict[str, Any]]:
        """Fallback: particiona código por blocos quando AST falha."""
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 para \n
            
            if current_size + line_size > max_size and current_chunk:
                # Salvar chunk atual
                chunk_text = '\n'.join(current_chunk)
                chunks.append({
                    "type": "block",
                    "symbol": f"block_{len(chunks)}",
                    "start_line": i - len(current_chunk),
                    "end_line": i - 1,
                    "text": chunk_text
                })
                
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Último chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                "type": "block",
                "symbol": f"block_{len(chunks)}",
                "start_line": len(lines) - len(current_chunk),
                "end_line": len(lines) - 1,
                "text": chunk_text
            })
        
        return chunks
    
    def _generate_file_summary(self, file_path: str, code: str, language: str) -> str:
        """Gera sumário de um arquivo."""
        try:
            # Extrair informações básicas
            lines = len(code.split('\n'))
            
            # Extrair símbolos principais
            ast_nodes = self._extract_ast_nodes(code, language)
            symbols = [node["symbol"] for node in ast_nodes if node["symbol"] != f"<{node['type']}>"]
            
            summary = f"Arquivo {file_path} ({language}, {lines} linhas)"
            if symbols:
                summary += f"\nSímbolos: {', '.join(symbols[:10])}"  # Primeiros 10
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar sumário: {e}")
            return f"Arquivo {file_path}"

    def index_file(self, file_path: str, repo_path: str) -> bool:
        """Indexa um arquivo específico."""
        try:
            # Ler arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Determinar linguagem
            language = self._get_language_from_extension(file_path)
            if not language:
                return False

            # Calcular hash do arquivo
            file_hash = hashlib.sha256(code.encode()).hexdigest()

            # Caminho relativo
            rel_path = os.path.relpath(file_path, repo_path)

            # Extrair chunks via AST
            ast_nodes = self._extract_ast_nodes(code, language)

            # Fallback para blocos se AST falhar
            if not ast_nodes:
                ast_nodes = self._chunk_by_blocks(code)

            # Indexar cada chunk
            points = []
            for i, node in enumerate(ast_nodes):
                chunk_text = node["text"]

                # Gerar embedding
                embedding = self.embedding_model.encode(chunk_text).tolist()

                # Criar ponto
                point_id = f"{file_hash}_{i}"
                payload = {
                    "path": rel_path,
                    "lang": language,
                    "symbol": node["symbol"],
                    "type": node["type"],
                    "sha": file_hash,
                    "text": chunk_text,
                    "start_byte": node.get("start_byte", 0),
                    "end_byte": node.get("end_byte", len(chunk_text)),
                    "start_line": node.get("start_line", 0),
                    "end_line": node.get("end_line", 0)
                }

                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))

            # Inserir no banco de vetores
            if points:
                self._upsert_vectors(points, "code")

            # Gerar e indexar sumário do arquivo
            summary = self._generate_file_summary(rel_path, code, language)
            summary_embedding = self.embedding_model.encode(summary).tolist()

            summary_point = PointStruct(
                id=f"file_{file_hash}",
                vector=summary_embedding,
                payload={
                    "path": rel_path,
                    "type": "file",
                    "summary": summary,
                    "lang": language,
                    "sha": file_hash
                }
            )

            self._upsert_vectors([summary_point], "summaries")

            logger.info(f"Indexado: {rel_path} ({len(points)} chunks)")
            return True

        except Exception as e:
            logger.error(f"Erro ao indexar {file_path}: {e}")
            return False

    def index_repository(self, repo_path: str, rebuild: bool = False) -> Dict[str, Any]:
        """Indexa um repositório completo."""
        repo_path = Path(repo_path).resolve()

        if rebuild:
            # Limpar coleções/índices
            try:
                self._clear_collections()
                self._ensure_collections()
                console.print("[yellow]Coleções/índices recriados[/yellow]")
            except Exception as e:
                logger.warning(f"Erro ao limpar coleções: {e}")

    def _clear_collections(self):
        """Limpa coleções/índices existentes."""
        if self.vector_backend == "qdrant":
            try:
                self.vector_client.delete_collection(self.collection_code)
            except Exception:
                pass
            try:
                self.vector_client.delete_collection(self.collection_summaries)
            except Exception:
                pass

        elif self.vector_backend == "pinecone":
            try:
                self.pinecone_client.delete_index(self.pinecone_index)
                # Aguardar exclusão
                import time
                time.sleep(10)
            except Exception:
                pass

        # Encontrar arquivos suportados
        supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx"}
        files_to_index = []

        for root, dirs, files in os.walk(repo_path):
            # Ignorar diretórios comuns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'
            }]

            for file in files:
                if Path(file).suffix.lower() in supported_extensions:
                    files_to_index.append(os.path.join(root, file))

        # Indexar arquivos
        indexed_count = 0
        failed_count = 0

        console.print(f"[blue]Indexando {len(files_to_index)} arquivos...[/blue]")

        for file_path in track(files_to_index, description="Indexando..."):
            if self.index_file(file_path, str(repo_path)):
                indexed_count += 1
            else:
                failed_count += 1

        # Gerar sumários de diretórios
        self._generate_directory_summaries(repo_path)

        result = {
            "repo_path": str(repo_path),
            "total_files": len(files_to_index),
            "indexed": indexed_count,
            "failed": failed_count,
            "success": failed_count == 0
        }

        console.print(f"[green]Indexação concluída: {indexed_count}/{len(files_to_index)} arquivos[/green]")

        return result

    def _generate_directory_summaries(self, repo_path: Path):
        """Gera sumários hierárquicos de diretórios."""
        try:
            # Coletar estrutura de diretórios
            dir_structure = {}

            for root, dirs, files in os.walk(repo_path):
                rel_root = os.path.relpath(root, repo_path)
                if rel_root == ".":
                    rel_root = ""

                # Filtrar arquivos relevantes
                relevant_files = [f for f in files if Path(f).suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx"}]

                if relevant_files:
                    dir_structure[rel_root] = {
                        "files": relevant_files,
                        "subdirs": [d for d in dirs if not d.startswith('.')]
                    }

            # Gerar sumários
            for dir_path, info in dir_structure.items():
                summary = f"Diretório: {dir_path or 'raiz'}\n"
                summary += f"Arquivos: {', '.join(info['files'][:10])}\n"
                if info['subdirs']:
                    summary += f"Subdiretórios: {', '.join(info['subdirs'][:5])}"

                # Gerar embedding e indexar
                embedding = self.embedding_model.encode(summary).tolist()
                dir_hash = hashlib.sha256(dir_path.encode()).hexdigest()

                self.qdrant.upsert(
                    collection_name=self.collection_summaries,
                    points=[PointStruct(
                        id=f"dir_{dir_hash}",
                        vector=embedding,
                        payload={
                            "path": dir_path,
                            "type": "directory",
                            "summary": summary,
                            "files": info['files'],
                            "subdirs": info['subdirs']
                        }
                    )]
                )

            logger.info(f"Sumários de {len(dir_structure)} diretórios gerados")

        except Exception as e:
            logger.error(f"Erro ao gerar sumários de diretórios: {e}")


def index_repository(repo_path: str, rebuild: bool = False) -> Dict[str, Any]:
    """Função de conveniência para indexar repositório."""
    indexer = CodeIndexer()
    return indexer.index_repository(repo_path, rebuild)
