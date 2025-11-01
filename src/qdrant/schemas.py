from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class SearchFilter:
    """filter for search queries"""
    must: Optional[List[Dict[str, Any]]] = None
    must_not: Optional[List[Dict[str, Any]]] = None
    should: Optional[List[Dict[str, Any]]] = None


@dataclass
class SearchResult:
    """result from vector search"""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None