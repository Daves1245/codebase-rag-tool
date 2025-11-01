import asyncio
from typing import List, Optional
from loguru import logger
import torch

from src.core.config import settings

from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    def __init__(self) -> None:
        self.provider = settings.EMBEDDING_PROVIDER
        self.model_name = settings.EMBEDDING_MODEL
        self.batch_size = settings.BATCH_SIZE
        self.model: Optional[SentenceTransformer] = None

        if self.provider == 'sentence-transformers':
            self._init_sentence_transformers()

    def _init_sentence_transformers(self) -> None:
        try:
            logger.info(f"Loading embedding model...")
            self.model = SentenceTransformer(self.model_name)

            # Use GPU if we can
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("Using GPU for embeddings")
            else:
                logger.info("Using CPU for embeddings")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.model_name == 'sentence-transformers':
            return await self._generate_st_embeddings(texts)
        elif self.model_name == 'openai':
            return await self._generate_openai_embeddings(texts)
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

    async def _generate_st_embeddings(self, texts: List[str]) -> List[List[float]]:
        event_loop = asyncio.get_event_loop()

        def _encode() -> List[List[float]]:
            embeddings = self.model.encode(
                texts,
                batch_size = self.batch_size,
                convert_to_numpy = True
            )
        ret = await event_loop.run_in_executor(None, _encode)
        pass

    async def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("Not yet implemented")

    async def generate_single_embedding(self, text: str) -> List[float]:
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
