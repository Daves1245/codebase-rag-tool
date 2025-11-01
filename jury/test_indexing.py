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

        # override config for testing
        from src.core.config import settings
        settings.EMBEDDING_PROVIDER = "mock"

        rag = CodebaseRAG()
        await rag.init()

        github_url = "https://github.com/Daves1245/horizon"

        result = await rag.index_repo(github_url, force_reindex=True)

        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_rag_initialization(self):
        """Test that RAG pipeline initializes correctly"""
        # override config for testing
        from src.core.config import settings
        settings.EMBEDDING_PROVIDER = "mock"

        rag = CodebaseRAG()
        await rag.init()

        assert rag.qdrant is not None
        assert rag.embeddings is not None
        assert rag.chunker is not None
        assert rag.git_handler is not None

# manual test development
async def manual_test_indexing():
    init_logger()
    print("testing rag indexing with github repository...")

    try:
        from src.core.config import settings
        settings.EMBEDDING_PROVIDER = "mock"

        rag = CodebaseRAG()
        print("rag pipeline created")

        await rag.init()
        print("rag pipeline initialized")

        github_url = "https://github.com/Daves1245/horizon"
        print(f"starting indexing of {github_url}...")

        result = await rag.index_repo(github_url, force_reindex=True)
        print(f"indexing completed successfully: {result}")
        return True
    except Exception as e:
        import traceback
        print(f"indexing failed: {e}")
        print("full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(manual_test_indexing())
    if success:
        print("CLI tool indexing test passed")
    else:
        print("CLI tool indexing test failed")
