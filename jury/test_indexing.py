import asyncio
import pytest
import sys
from pathlib import Path

# neded for pytest resolution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.rag_pipeline import CodebaseRAG
from src.utils.logger import init_logger

class TestIndexing:
    @pytest.mark.asyncio
    async def test_github_repo_indexing(self):
        """Test indexing of the GitHub repository https://github.com/Daves1245/horizon"""
        init_logger()

        rag = CodebaseRAG()
        await rag.init()

        github_url = "https://github.com/Daves1245/horizon"

        result = await rag.index_repo(github_url, force_reindex=True)

        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_rag_initialization(self):
        """Test that RAG pipeline initializes correctly"""
        rag = CodebaseRAG()
        await rag.init()

        assert rag.qdrant is not None
        assert rag.embeddings is not None
        assert rag.chunker is not None
        assert rag.git_handler is not None

# manual test development
async def manual_test_indexing():
    init_logger()
    print("Testing RAG indexing with GitHub repository...")

    rag = CodebaseRAG()
    await rag.init()

    github_url = "https://github.com/Daves1245/horizon"
    try:
        result = await rag.index_repo(github_url, force_reindex=True)
        print(f"Indexing completed successfully: {result}")
        return True
    except Exception as e:
        print(f"Indexing failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(manual_test_indexing())
    if success:
        print("CLI tool indexing test passed")
    else:
        print("CLI tool indexing test failed")
