from pathlib import Path
from typing import List, Optional

from src.core.ast_parser import ASTMetadata
from src.core.config import settings

from loguru import logger

class Chunk:
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str # block, overlap, etc.
    symbol_name: Optional[str] = None
    docstring: Optional[str] = None
    ast_metadata: Optional[dict] = None
    pass

class Chunker:
    def __init__(self) -> None:
        self.chunk_size = settings.CHUNK_SIZE
        self.overlap = settings.CHUNK_OVERLAP

    def chunk_file(self, path: Path, content: str, ast_metadata: Optional[ASTMetadata]) -> List[Chunk]:
        # TODO implement more thorough chunking strategy. see ZeroEntropy docs
        lines = content.splitlines(keepends=True)
        chunks: List[Chunk] = []
        language = self._detect_language(path)
        if ast_metadata and ast_metadata.symbols:
            chunks.extend(self._chunk_by_symbols(path, lines, language, ast_metadata))
        else:
            # fallback
            chunks.extend(self._chunk_by_line(path, lines, language, ast_metadata))

        logger.debug(f"Created {len(chunks)} chunks from {path}")

        return chunks

    def _chunk_by_symbols(self, path: Path, lines: str, language: str, ast_metadata: Optional[dict] = None) -> List[Chunk]:
        chunks: List[Chunk] = []
        return chunks

    def _chunk_by_line(self, path: Path, lines: str, language: str, ast_metadata: Optional[dict] = None) -> List[Chunk]:
        chunks: List[Chunk] = []
        return chunks

    pass
