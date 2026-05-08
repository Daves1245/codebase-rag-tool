"""
query_rewriter: Reshape user inputs into a form that will likely generate better results
"""
from dataclasses import dataclass
from typing import List, Literal, Protocol

from anthropic import Anthropic

from loguru import logger
from src.config.settings import Config, Credentials

settings = Config.load()
credentials = Credentials.load()

@dataclass
class TransformedQuery:
    """Result of a query strategy: the inputs a retriever should actually search with."""
    original_query: str
    expanded_terms: List[str]
    search_strategy: Literal['ast', 'semantic', 'hybrid']
    file_patterns: List[str]
    reasoning: str


# use a protocol since each strategy doesn't have enough
# overlap and we only want to specify a transform() interface
class QueryStrategy(Protocol):  # pylint: disable=too-few-public-methods
    """Structural type for any query-transformation strategy."""

    async def transform(self, query: str) -> TransformedQuery:
        """Transform a raw user query into a TransformedQuery for retrieval."""


class PassthroughStrategy:  # pylint: disable=too-few-public-methods
    """No-op strategy: returns the raw query unchanged. Baseline / fallback."""

    async def transform(self, query: str) -> TransformedQuery:
        """Wrap the query in a TransformedQuery without invoking an LLM."""
        return TransformedQuery(
            original_query=query,
            expanded_terms=[query],
            search_strategy='hybrid',
            file_patterns=[],
            reasoning="passthrough",
        )


class HyDEStrategy:  # pylint: disable=too-few-public-methods
    """Hypothetical Document Embeddings: ask the LLM to draft a synthetic answer
    document and use it as the semantic-search input. See https://arxiv.org/pdf/2212.10496."""

    def __init__(self, client: Anthropic, model: str) -> None:
        self.client = client
        self.model = model

    async def transform(self, query: str) -> TransformedQuery:
        """Generate a hypothetical code snippet that would answer `query`."""
        # TODO: prompt LLM for a hypothetical code snippet that would answer `query`,
        # return its text as a semantic input for the embedder
        raise NotImplementedError


class RewriteStrategy:  # pylint: disable=too-few-public-methods
    """LLM-based query expansion: rewrite the query into related terms and file patterns."""

    def __init__(self, client: Anthropic, model: str) -> None:
        self.client = client
        self.model = model

    async def transform(self, query: str) -> TransformedQuery:
        """Expand `query` into related terms / file patterns via the LLM."""
        # TODO: prompt LLM to expand `query` into related terms / file patterns,
        # parse JSON response into TransformedQuery
        raise NotImplementedError


class CompositeStrategy:  # pylint: disable=too-few-public-methods
    """Fan out to several strategies in parallel and merge their TransformedQuery outputs."""

    def __init__(self, strategies: List[QueryStrategy]) -> None:
        self.strategies = strategies

    async def transform(self, query: str) -> TransformedQuery:
        """Run each child strategy on the raw query and merge the results."""
        # TODO: run each strategy on the raw query in parallel,
        # merge expanded_terms / file_patterns, pick a search_strategy
        raise NotImplementedError


class QueryRewriter:  # pylint: disable=too-few-public-methods
    """Selects a QueryStrategy from settings and dispatches the raw query through it."""

    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.model = settings.llm_model

        if self.provider == 'anthropic':
            api_key = credentials.api_key.get_secret_value()  # pylint: disable=no-member
            if not api_key:
                logger.warning("No api key configured, query rewriting disabled")
                self.client = None
            else:
                self.client = Anthropic(api_key=api_key)
        else:
            logger.warning(f"Provider not yet supported: {settings.llm_provider}")

    async def rewrite_query(self, original_query: str) -> TransformedQuery:
        """
        Rewrite the original user query to hopefully generate better results

        Query rewriting pipeline:
        raq query -> strategy (one of below) -> TransformedQuery -> retrieval


        We use a couple of techniques:
        - HyDE (hypothetical document embeddings): https://arxiv.org/pdf/2212.10496
            Notes:
                * adds an extra LLM call, good for short user queries on large corpuses
                * works well in knowledge-dense domains, or when user queries don't use
                  the same vocabulary as the corpus
        - Rewrite:
            Rewrite the query text to remove irrelevant context, add relevant ones, etc
        - Passthrough - no change, just pass the original query through

        """
        strategy = self._select_strategy(settings.strategy)
        return await strategy.transform(original_query)

    def _select_strategy(self, name: str) -> QueryStrategy:
        # without an LLM client, only passthrough is viable
        if self.client is None and name != 'passthrough':
            logger.warning(f"Strategy '{name}' requires an LLM client; falling back to passthrough")
            return PassthroughStrategy()

        if name == 'passthrough':
            return PassthroughStrategy()
        if name == 'hyde':
            return HyDEStrategy(self.client, self.model)
        if name == 'rewrite':
            return RewriteStrategy(self.client, self.model)
        if name == 'composite':
            return CompositeStrategy([
                RewriteStrategy(self.client, self.model),
                HyDEStrategy(self.client, self.model),
            ])
        raise ValueError(f"Unknown query strategy: {name!r}")
