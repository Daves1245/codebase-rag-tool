import asyncio
from typing import List, Dict, Any
from loguru import logger
from qdrant_client import QdrantClient as QdrantClientLib
from qdrant_client.models import Distance, VectorParams
from src.core.config import settings

class QdrantClient:
    def __init__(self):
        self.client = QdrantClientLib(":memory:")  # use in-memory for testing
        self.collection_name = "codebase_vectors"

    async def create_collection(self) -> None:
        """create vector collection"""
        try:
            # check if collection exists
            collections = self.client.get_collections()
            if any(c.name == self.collection_name for c in collections.collections):
                logger.info(f"collection {self.collection_name} already exists")
                return

            # create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"created collection {self.collection_name}")
        except Exception as e:
            logger.error(f"failed to create collection: {e}")
            raise

    async def upsert_chunks(self, repo_id: str, chunks: List[Any], embeddings: List[List[float]]) -> None:
        """insert or update chunk vectors"""
        if not chunks or not embeddings:
            logger.warning("no chunks or embeddings to upsert")
            return

        if len(chunks) != len(embeddings):
            raise ValueError(f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) length mismatch")

        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append({
                "id": f"{repo_id}_{i}",
                "vector": embedding,
                "payload": {
                    "repo_id": repo_id,
                    "file_path": str(chunk.file_path) if hasattr(chunk, 'file_path') else "",
                    "content": chunk.content if hasattr(chunk, 'content') else str(chunk),
                    "start_line": getattr(chunk, 'start_line', 0),
                    "end_line": getattr(chunk, 'end_line', 0)
                }
            })

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"upserted {len(points)} chunks for repo {repo_id}")

    async def search(self, query_embedding: List[float], top_k: int = 5, repo_filter: str = None) -> List[Dict[str, Any]]:
        """search for similar vectors"""
        try:
            search_filter = None
            if repo_filter:
                search_filter = {
                    "must": [{"key": "repo_id", "match": {"value": repo_filter}}]
                }

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"search failed: {e}")
            return []
