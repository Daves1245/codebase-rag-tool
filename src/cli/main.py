import asyncio
import click

from src.core.config import settings
from src.core.rag_pipeline import CodebaseRAG
from src.utils.logger import init_logger

def cli():
    welcome_message = "codbease rag tool"
    print(welcome_message)
    init_logger()

def index(github_url: str) -> None:
    rag = CodebaseRAG()
    async def run_index(github_url: str) -> str:
        await rag.init()
        return await rag.index_repo(github_url)

def query(repo_id: str, query: str, top_k: int = 5, mode: str = "hybrid") -> None:
    rag = CodebaseRAG()
    async def run_query() -> None:
        await rag.init()
        return await rag.query(repo_id, query, top_k, mode)
    result = asyncio.run(run_query())

    if not result.results:
        print("No results found")

    if result.generated_response:
        print("Refined query: ", result.generated_response)
    for i, res in enumerate(result.results, 1):
        print("Score: ", res.score)
        print("```")
        print(res.content)
        print("```")


if __name__ == "__main__":
    cli()
