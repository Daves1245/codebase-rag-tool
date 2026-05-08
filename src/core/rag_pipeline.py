"""RAG pipeline for codebase search and retrieval."""
import time
from dataclasses import dataclass
from typing import List, Optional, Literal

from loguru import logger

from src.core.ast_parser import ASTParser
from src.core.chunker import Chunker, Chunk
from src.core.embeddings import EmbeddingGenerator
from src.core.git_handler import GitHandler
from src.core.hybrid_search import HybridSearch, SearchResult
from src.core.query_rewriter import QueryRewriter, TransformedQuery
from src.core.response_generator import ResponseGenerator
from src.qdrant.qdrant_client import QdrantClient


@dataclass
class QueryResult:
    """Result of a query operation."""

    query: str
    rewritten_query: TransformedQuery
    results: List[SearchResult]
    search_time_ms: float
    search_mode: str
    generated_response: Optional[str] = None


class CodebaseRAG:  # pylint: disable=too-many-instance-attributes
    """Main RAG pipeline for codebase search."""

    def __init__(self) -> None:
        """Initialize the RAG pipeline components."""
        self.query_rewriter = QueryRewriter()
        self.qdrant = QdrantClient()
        self.hybrid_search = HybridSearch(self.qdrant)
        self.response_generator = ResponseGenerator()
        self.chunker = Chunker()
        self.embeddings = EmbeddingGenerator()
        self.ast_parser = ASTParser()
        self.git_handler = GitHandler()

        logger.info("RAG pipeline initialized")

    async def init(self) -> None:
        """Create necessary Qdrant collections."""
        await self.qdrant.create_collection()
        logger.info("RAG pipeline ready")

    async def index_repo(self, github_url: str, force_reindex: bool = False) -> str:
        """Clone and index a GitHub repository, returning the repo_id."""
        logger.info(f"Indexing repository: {github_url}")

        repo_id, repo_path = await self.git_handler.clone_repo(github_url)

        if force_reindex:
            self.git_handler.delete_repo(repo_id)
            repo_id, repo_path = await self.git_handler.clone_repo(github_url)

        files = [p for p in repo_path.rglob("*") if p.is_file()]
        logger.info(f"Found {len(files)} files")

        if not files:
            raise ValueError("No files found in repo")

        chunks: List[Chunk] = []

        for path in files:
            logger.info(f"Chunking {path}")
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                ast_metadata = self.ast_parser.parse_file(path, content)
                file_chunks = self.chunker.chunk_file(
                    path.relative_to(repo_path),
                    content,
                    ast_metadata,
                )
                chunks.extend(file_chunks)
            except OSError as e:
                logger.error(f"Failed to index {path}: {e}")

        logger.info(f"Created {len(chunks)} code chunks")

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await self.embeddings.generate_embeddings(chunk_texts)

        await self.qdrant.upsert_chunks(repo_id, chunks, embeddings)

        logger.info(f"Indexed repo {repo_id}")
        return repo_id

    async def query(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        repo_id: str,
        query: str,
        top_k: int = 5,
        search_mode: Literal["hybrid", "test", "semantic"] = "hybrid",
        generate_response: bool = False,
    ) -> QueryResult:
        """Run a search query against an indexed repository."""
        start_time = time.time()
        logger.info(f"Query: {query} on repo: {repo_id}")
        try:
            rewritten = await self.query_rewriter.rewrite_query(query)
            if search_mode != "hybrid":
                rewritten.search_strategy = search_mode
            embedding = await self.embeddings.generate_single_embedding(query)
            results = await self.hybrid_search.search(
                repo_id=repo_id,
                query_vector=embedding,
                rewritten_query=rewritten,
                top_k=top_k,
            )
            search_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Finished query in {search_time_ms:.0f}ms, "
                f"found {len(results)} results"
            )

            generated = None
            if generate_response and results:
                try:
                    generated = await self.response_generator.generate_response(
                        query, results
                    )
                    logger.info("Response generated")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.warning(f"Response generation failed: {e}")
            return QueryResult(
                query=query,
                rewritten_query=rewritten,
                results=results,
                search_time_ms=search_time_ms,
                search_mode=search_mode,
                generated_response=generated,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Query failed: {e}")
            raise
