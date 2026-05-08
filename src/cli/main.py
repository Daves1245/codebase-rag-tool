"""
main.py: entrypoint for cli
"""
import asyncio

from src.core.rag_pipeline import CodebaseRAG
from src.utils.logger import init_logger

def cli():
    init_logger()

# these functions are declared synchronous because we plan to use
# a CLI entrypoint that expects these to be synchronous - I believe
# this is a standard bridge, to use asyncio as a wrapper. async
# is necessary at least, since index() and query() do I/O operations
# like network calls and vector db queries
def index(github_url: str) -> None:
    """
    index: given a github repo url, index it and add it to qdrant
    """
    rag = CodebaseRAG()
    async def run_index(github_url: str) -> str:
        await rag.init()
        return await rag.index_repo(github_url, force_reindex=False)
    asyncio.run(run_index(github_url))

def query(repo_id: str, query_text: str, top_k: int = 5, mode: str = "hybrid") -> None:
    """
    query: given a repo id and query, return `top_k` elements that best answer the query text

    Args:
        top_k: number of entries to return
        mode: one of `search_mode` values: semantic, sparse, or hybrid searches
    """
    rag = CodebaseRAG()
    async def run_query() -> None:
        await rag.init()
        return await rag.query(repo_id, query_text, top_k, mode)
    result = asyncio.run(run_query())

    if not result.results:
        print("No results found")

    if result.generated_response:
        print("Refined query: ", result.generated_response)
    for res in enumerate(result.results, 1):
        print("Score: ", res.score)
        print("```")
        print(res.content)
        print("```")


if __name__ == "__main__":
    cli()
