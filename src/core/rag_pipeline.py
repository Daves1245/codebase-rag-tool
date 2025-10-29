import asyncio
from typing import List, Optional

from loguru import logger

from src.core.ast_parser import ASTParser
from src.core.chunker import Chunker, Chunk
from src.core.config import settings
from src.core.embeddings import EmbeddingGenerator
from src.core.git_handler import GitHandler
from src.core.hybrid_search import HybridSearch, SearchResult
from src.core.query_rewriter import QueryRewriter, RewrittenQuery
from src.core.response_generator import ResponseGenerator
from src.qdrant.qdrant_client import QdrantClient

class QueryResult:
    """Result of a query operation."""
    query: str
    rewritten_query: RewrittenQuery
    results: List[SearchResult]
    search_time_ms: float
    search_mode: str
    generated_response: Optional[str] = None

class CodebaseRAG:
    def __init__(self) -> None:
        self.query_refiner = QueryRefiner()
        self.hybrid_search = HybridSearch()
        self.response_generator = ResponseGenerator()
        self.chunker = Chunker()
        self.ast_parser = ASTParser()
        self.git_handler = GitHandler()

        logger.info("RAG pipeline initialized")

class QueryRefiner:
    pass
