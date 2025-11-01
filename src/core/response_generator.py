from typing import List
from loguru import logger
from anthropic import Anthropic

from src.core.config import settings
from src.core.hybrid_search import SearchResult

class ResponseGenerator:
    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL

        logger.info(f"[ResponseGenerator]:: provider = {self.provider}")

        if self.provider == "anthropic":
            if not settings.LLM_API_KEY or settings.LLM_API_KEY.strip() == "":
                logger.warning("no anthropic api key configured, response generation disabled")
                self.client = None
            else:
                try:
                    logger.info(f"initializing anthropic client...")
                    self.client = Anthropic(api_key=settings.LLM_API_KEY)
                    logger.info("anthropic clien initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize anthropic client: {e}")
                    self.client = None
        else:
            logger.warning(f"Unsupported LLM provider: {self.provider}")
            self.client = None

    async def generate_response(
        self,
        query: str,
        search_results: List[SearchResult],
        max_tokens: int = 2000
    ) -> str:

        if not self.client:
            return self._fallback_response(query, seach_results)

        if not search_results:
            return "No relevant answer found"

        try:
            prompt = self._build_prompt(query, search_results)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": "prompt"}]
            )

            answer = response.content[0].text
            logger.info(f"Generated response for query: {query}")
            return answer
        except Exception as e:
            logger.error(f"Response generation failed: {e}")

    def _build_prompt(self, query: str, search_results: List[SearchResult]) -> str:
        code_context = []
        for i, result in enumerate(search_results[:5], 1):
            code_context.append(
                f"### Code Snippet {i}\n"
                f"File: {result.file_path} (lines {result.start_line}-{result.end_line})\n"
                f"Language: {result.language}\n"
                f"```{result.language}\n{result.content}\n```\n"
            )

        context_text = "\n".join(code_context)
        return f"""You are a helpful code assistant. A user is asking a question about a codebase. 
I've retrieved the most relevant code snippets. Please provide a clear, concise answer to their question based on these code snippets.

**User Question:** {query}

**Retrieved Code:**
{context_text}

**Instructions:**
1. Answer the user's question directly and concisely
2. Reference specific code snippets when relevant (e.g., "In file.py, lines 10-20...")
3. Explain what the code does in plain language
4. If the code doesn't fully answer the question, say so
5. Keep your answer focused and practical
6. Use markdown formatting for code references

**Your Answer:**"""

    def _fallback_response(self, query: str, search_results: List[SearchResult]) -> str:
        if not search_results:
            return "No relevant answer found"
        response = f"Found {len(search_results)} relevant code snippet(s):\n\n"
        for i, result in enumerate(search_results[:3], 1):
            if result.symbol_name:
                response += f" Symbol: `{result.symbol_name}`\n"
            response += "\n"
        response += "\n*Enable LLM API key for detailed natural language answers.*"
        return response
