"""Embedding generation supporting sentence-transformers, zembed, and mock providers."""
import asyncio
from typing import Dict, List, Literal, Optional

from loguru import logger

from src.config.settings import Config

_config = Config.load()

# Maps known model names to their output dimensions.
# Used to validate/override settings.EMBEDDING_DIMENSION at init time.
MODEL_DIMENSIONS: Dict[str, int] = {
    "zeroentropy/zembed-1-embedding": 2560,
    "zeroentropy/zembed-1": 2560,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    "sentence-transformers/all-distilroberta-v1": 768,
}

InputType = Literal["query", "document"]


class EmbeddingGenerator:
    """Generates embeddings using a configured provider and model."""

    def __init__(self) -> None:
        """Load the configured embedding model."""
        self.provider = _config.embedding_provider
        self.model_name = _config.embedding_model
        self.batch_size = _config.batch_size
        self.model: Optional[object] = None

        known_dim = MODEL_DIMENSIONS.get(self.model_name)
        if known_dim and known_dim != _config.embedding_dimensions:
            logger.warning(
                f"embedding_dimensions={_config.embedding_dimensions} does not match "
                f"{self.model_name} native dimension {known_dim}. "
                "Update EMBEDDING_DIMENSION in config to avoid Qdrant shape mismatches."
            )

        if self.provider == "sentence-transformers":
            self._init_sentence_transformers()
        elif self.provider == "zembed":
            self._init_zembed()
        elif self.provider == "mock":
            self._init_mock_embeddings()

    def _init_sentence_transformers(self) -> None:
        """Load a HuggingFace model via sentence-transformers."""
        try:
            import torch  # pylint: disable=import-outside-toplevel
            from sentence_transformers import SentenceTransformer  # pylint: disable=import-outside-toplevel

            logger.info(f"Loading embedding model {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)

            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("Using GPU for embeddings")
            else:
                logger.info("Using CPU for embeddings")

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Failed to load embedding model: {e}")
            logger.info("Falling back to mock embeddings")
            self._init_mock_embeddings()

    def _init_zembed(self) -> None:
        """Load zembed-1 via sentence-transformers with required kwargs."""
        try:
            import torch  # pylint: disable=import-outside-toplevel
            from sentence_transformers import SentenceTransformer  # pylint: disable=import-outside-toplevel

            model_id = self.model_name or "zeroentropy/zembed-1-embedding"
            logger.info(f"Loading zembed model {model_id}...")

            self.model = SentenceTransformer(
                model_id,
                trust_remote_code=True,
                model_kwargs={"torch_dtype": torch.bfloat16},
            )

            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("Using GPU for zembed")
            elif torch.backends.mps.is_available():
                self.model = self.model.to("mps")
                logger.info("Using MPS for zembed")
            else:
                logger.info("Using CPU for zembed")

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Failed to load zembed model: {e}")
            logger.info("Falling back to mock embeddings")
            self._init_mock_embeddings()

    def _init_mock_embeddings(self) -> None:
        """Switch to mock provider (used as fallback and in tests)."""
        logger.info("Using mock embeddings")
        self.provider = "mock"

    async def generate_embeddings(
        self,
        texts: List[str],
        input_type: InputType = "document",
    ) -> List[List[float]]:
        """Encode a batch of texts. Use input_type='query' for search queries."""
        if not texts:
            return []

        if self.provider == "sentence-transformers":
            return await self._generate_st_embeddings(texts)
        if self.provider == "zembed":
            return await self._generate_zembed_embeddings(texts, input_type)
        if self.provider == "mock":
            return await self._generate_mock_embeddings(texts)
        raise ValueError(f"Unknown embedding provider: {self.provider}")

    async def generate_single_embedding(self, text: str) -> List[float]:
        """Encode a single query string."""
        embeddings = await self.generate_embeddings([text], input_type="query")
        return embeddings[0] if embeddings else []

    async def _generate_st_embeddings(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()

        def _encode() -> List[List[float]]:
            return self.model.encode(
                texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
            ).tolist()

        return await loop.run_in_executor(None, _encode)

    async def _generate_zembed_embeddings(
        self,
        texts: List[str],
        input_type: InputType,
    ) -> List[List[float]]:
        """Encode using zembed's asymmetric query/document paths."""
        loop = asyncio.get_event_loop()

        def _encode() -> List[List[float]]:
            if input_type == "query":
                result = self.model.encode_query(
                    texts[0] if len(texts) == 1 else texts,
                )
            else:
                result = self.model.encode_document(texts)
            import numpy as np  # pylint: disable=import-outside-toplevel
            arr = np.array(result)
            return arr.tolist() if arr.ndim == 2 else [arr.tolist()]

        return await loop.run_in_executor(None, _encode)

    async def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Deterministic mock embeddings for testing."""
        import hashlib  # pylint: disable=import-outside-toplevel
        embeddings = []
        for text in texts:
            hash_bytes = hashlib.md5(text.encode()).digest()
            embedding = []
            for i in range(0, len(hash_bytes), 2):
                if i + 1 < len(hash_bytes):
                    embedding.append((hash_bytes[i] + hash_bytes[i + 1] * 256) / 65535.0)
            while len(embedding) < 384:
                embedding.append(0.0)
            embeddings.append(embedding[:384])
        return embeddings
