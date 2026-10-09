from .classifier import classify_change
from .matcher import DocumentMatcher
from .service import ComparisonService
from .strategies import ComparisonStrategy, SemanticComparisonStrategy, TextComparisonStrategy

__all__ = [
    "DocumentMatcher",
    "ComparisonService",
    "ComparisonStrategy",
    "TextComparisonStrategy",
    "SemanticComparisonStrategy",
    "classify_change",
]

