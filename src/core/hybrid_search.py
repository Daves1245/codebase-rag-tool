"""Hybrid search combining semantic vector search and AST-based retrieval."""
from dataclasses import dataclass, field
from typing import Optional, List, Literal, Dict, Any

from loguru import logger

from src.core.query_rewriter import TransformedQuery
from src.qdrant.qdrant_client import QdrantClient
from src.qdrant.schemas import SearchFilter


@dataclass
class SearchResult:  # pylint: disable=too-many-instance-attributes
    """Enriched search result returned to callers."""

    file_path: str
    content: str
    language: str
    start_line: int
    end_line: int
    score: float
    chunk_type: str
    source: Literal["ast", "semantic", "hybrid"]
    symbol_name: Optional[str] = None
    ast_metadata: Optional[Dict[str, Any]] = field(default=None)


class HybridSearch:  # pylint: disable=too-few-public-methods
    """Combines semantic and AST search with reciprocal rank fusion."""

    def __init__(self, qdrant_client: QdrantClient) -> None:
        self.qdrant = qdrant_client

    async def search(
        self,
        repo_id: str,
        query_vector: List[float],
        rewritten_query: TransformedQuery,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Run search using the strategy declared in rewritten_query."""
        semantic_results: List[SearchResult] = []
        ast_results: List[SearchResult] = []
        filters = self._build_filters(rewritten_query)

        if rewritten_query.search_strategy in ("semantic", "hybrid"):
            semantic_results = await self._semantic_search(
                repo_id, query_vector, top_k * 2, filters
            )

        if rewritten_query.search_strategy in ("ast", "hybrid"):
            try:
                ast_results = await self._ast_search(
                    repo_id, query_vector, top_k * 2, filters
                )
            except NotImplementedError:
                logger.debug("AST search not yet implemented, skipping")

        if rewritten_query.search_strategy == "hybrid" and semantic_results and ast_results:
            fused_results = self._reciprocal_rank_fusion(ast_results, semantic_results)
        elif semantic_results:
            fused_results = semantic_results
        elif ast_results:
            fused_results = ast_results
        else:
            fused_results = []

        return fused_results[:top_k]

    async def _semantic_search(
        self,
        repo_id: str,
        query_vector: List[float],
        limit: int,
        filters: SearchFilter,
    ) -> List[SearchResult]:
        """Vector similarity search via Qdrant, scoped to repo_id."""
        raw = await self.qdrant.search(query_vector, filters, limit)
        results = []
        for r in raw:
            if r.payload.get("repo_id") != repo_id:
                continue
            results.append(SearchResult(
                file_path=r.payload.get("file_path", ""),
                content=r.payload.get("content", ""),
                language=r.payload.get("language", ""),
                start_line=r.payload.get("start_line", 0),
                end_line=r.payload.get("end_line", 0),
                score=r.score,
                chunk_type=r.payload.get("chunk_type", "chunk"),
                source="semantic",
            ))
        return results

    async def _ast_search(
        self,
        repo_id: str,
        query_vector: List[float],
        limit: int,
        filters: SearchFilter,
    ) -> List[SearchResult]:
        raise NotImplementedError("AST search not yet implemented")

    @staticmethod
    def _reciprocal_rank_fusion(
        ast_results: List[SearchResult],
        semantic_results: List[SearchResult],
        k: int = 60,
    ) -> List[SearchResult]:
        """Merge two ranked lists using reciprocal rank fusion."""
        scores: Dict[str, tuple] = {}
        for rank, result in enumerate(semantic_results):
            key = f"{result.file_path}:{result.start_line}"
            prev_score = scores[key][1] if key in scores else 0.0
            scores[key] = (result, prev_score + 1.0 / (k + rank + 1))
        for rank, result in enumerate(ast_results):
            key = f"{result.file_path}:{result.start_line}"
            prev_score = scores[key][1] if key in scores else 0.0
            scores[key] = (result, prev_score + 1.0 / (k + rank + 1))
        return [r for r, _ in sorted(scores.values(), key=lambda x: x[1], reverse=True)]

    def _build_filters(self, _rewritten_query: TransformedQuery) -> SearchFilter:
        """Build a Qdrant SearchFilter from query metadata."""
        return SearchFilter()
