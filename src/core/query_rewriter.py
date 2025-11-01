from dataclasses import dataclass
from typing import Optional, List, Literal

from anthropic import Anthropic

from loguru import logger
from src.core.config import settings

@dataclass
class RewrittenQuery:
    original_query: str
    expanded_terms: List[str]
    search_strategy: Literal['ast', 'semantic', 'hybrid']
    file_patterns: List[str]
    reasoning: str
    pass

class QueryRewriter:
    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL

        if self.provider == 'anthropic':
            if not settings.LLM_API_KEY:
                logger.warning("No api key configured, query rewriting disabled")
                self.client = None
            else:
                self.client = Anthropic(api_key=settings.LLM_API_KEY)
        else:
            logger.warning(f"Provider not yet supported: {settings.LLM_PROVIDER}")

    async def rewrite_query(self, original_query) -> RewrittenQuery:
        if not self.client:
            # Return basic query without rewriting
            return RewrittenQuery(
                original_query=original_query,
                expanded_terms=[original_query],
                search_strategy='hybrid',
                file_patterns=[],
                reasoning="Query rewriting not available"
            )

        try:
            prompt = self._build_rewrite_prompt(original_query)
            response = self.client.messages.create(
                model = self.model,
                max_tokens = 1000,
                messages=[{"role": "user", "content": prompt}]
            )

            rewritten = self._parse_rewrite_response(
                original_query,
                response.content[0].text
            )

            logger.debug(f"Rewrote query: {original_query} -> {rewritten.expanded_terms}")
            return rewritten

        except Exception as e:
            logger.error(f"Query rewriting failed: {e}")
            # Fallback to original query
            return RewrittenQuery(
                original_query=original_query,
                expanded_terms=[original_query],
                search_strategy='hybrid',
                file_patterns=[],
                reasoning=f"Rewriting failed: {e}"
            )

        except Exception as e:
