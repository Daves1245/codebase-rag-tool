import asyncio
from typing import List, Optional
from loguru import logger

from src.core.config import settings

class EmbeddingGenerator:
    def __init__(self) -> None:
        self.provider = settings.EMBEDDING_PROVIDER
        self.model_name = settings.EMBEDDING_MODEL
        self.batch_size = settings.BATCH_SIZE
        self.model: Optional[object] = None

        if self.provider == 'sentence-transformers':
            self._init_sentence_transformers()
        elif self.provider == 'mock':
            self._init_mock_embeddings()

    def _init_sentence_transformers(self) -> None:
        try:
            # lazy import to avoid segfaults during testing
            import torch
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"loading embedding model...")
            self.model = SentenceTransformer(self.model_name)

            # use gpu if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("using gpu for embeddings")
            else:
                logger.info("using cpu for embeddings")

        except Exception as e:
            logger.error(f"failed to load embedding model: {e}")
            logger.info("falling back to mock embeddings")
            self._init_mock_embeddings()

    def _init_mock_embeddings(self) -> None:
        logger.info("using mock embeddings for testing")
        self.provider = 'mock'

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.provider == 'sentence-transformers':
            return await self._generate_st_embeddings(texts)
        elif self.provider == 'mock':
            return await self._generate_mock_embeddings(texts)
        elif self.provider == 'openai':
            return await self._generate_openai_embeddings(texts)
        else:
            raise ValueError(f"unknown embedding provider: {self.provider}")

    async def _generate_st_embeddings(self, texts: List[str]) -> List[List[float]]:
        event_loop = asyncio.get_event_loop()

        def _encode() -> List[List[float]]:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        
        return await event_loop.run_in_executor(None, _encode)

    async def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        # return mock embeddings for testing
        import hashlib
        embeddings = []
        for text in texts:
            # create deterministic mock embedding based on text hash
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # convert to 384-dimensional float vector
            embedding = []
            for i in range(0, len(hash_bytes), 2):
                if i + 1 < len(hash_bytes):
                    val = (hash_bytes[i] + hash_bytes[i+1] * 256) / 65535.0
                    embedding.append(val)
            # pad to 384 dimensions
            while len(embedding) < 384:
                embedding.append(0.0)
            embeddings.append(embedding[:384])
        return embeddings

    async def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("openai embeddings not yet implemented")

    async def generate_single_embedding(self, text: str) -> List[float]:
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
