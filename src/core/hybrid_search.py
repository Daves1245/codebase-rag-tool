from typing import Optional, List, Literal, Dict, Any
from dataclasses import dataclass
from loguru import logger

from src.core.ast_parser import ASTMetadata

from src.core.query_rewriter import RewrittenQuery
from src.qdrant.qdrant_client import QdrantClient
from src.qdrant.schemas import SearchFilter

class SearchResult:
    file_path: str
    content: str
    language: str
    start_line: int
    end_line: int
    score: float
    chunk_type: str
    symbol_name: Optional[str]
    source: Literal['ast', 'semantic', 'hybrid']
    ast_metadata: Optional[Dict[str, Any]] = None

class HybridSearch:
    def __init__(self, qdrant_client: QdrantClient) -> None:
        self.qdrant = qdrant_client
    async def search(
        self,
        repo_id: str,
        query_vector: List[float],
        rewritten_query: str,
        top_k: int = 5
    ) -> None:

        semantic_results: List[SearchResult] = []
        ast_results: List[ASTMetadata] = []
        filters = self._build_filters(rewritten_query)

        # semantic search
        if rewritten_query.search_strategy in ['semantic', 'hybdrid']:
            semantic_results = await self._semantic_search(
                repo_id,
                query_vector,
                top_k * 2, # used for fusion
                filters
            )

        # ast search
        if rewritten_query.search_strategy in ['ast', 'hybrid']:
            ast_results = await self._ast_search(
                repo_id,
                query_vector,
                top_k * 2,
                filters
            )

        # fuse results
        if rewritten_query.search_strategy == 'hybrid' and semantic_results and ast_results:
            # oh man we can replace with zeroentropy here hehehehe
            # sooon.
            fused = self.reciprocal_rank_fusion(
    ast_results,
                semantic_results
            )
        elif semantic_results:
            fused_results = semantic_results
        elif ast_results:
            fused_results = ast_results
        else:
            fused_results = []
        return fused[:top_k]

    def ast_search(
        self,
        repo_id: str,
        rewritten_query: str,
        limit: int,
        filters: SearchFilter
    ) -> List[SearchResult]:
        raise NotImplementedError("AST Search not yet implemented")

    def hybrid_search(
        self,
        repo_id: str,
        rewritten_query: str,
        limit: int,
        filters: SearchFilter
    ) -> List[SearchResult]:
        raise NotImplementedError("Hybrid Search not yet implemented")

    def semantic_search(
        self,
        repo_id: str,
        rewritten_query: str,
        limit: int,
        filters: SearchFilter
    ) -> List[SearchResult]:
        raise NotImplementedError("Semantic Search not yet implemented")

    async def reciprocal_rank_fusion(
        self,
        ast_results: List[SearchResult],
        semantic_results: List[SearchResult],
        k: int = 60
    ) -> List[SearchResult]:
        raise NotImplementedError("RRF not yet implemented")

    def _build_filters(self, rewritten_query: str) -> SearchFilter:
        filters = SearchFilter()
        # TODO parse file and add language/path filters
        return filters
