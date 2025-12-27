"""
Search Strategy Registry

Defines swappable search strategies for evaluation and comparison.
Each strategy configures different weights, thresholds, and post-processing.
"""

import math
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any
from enum import Enum

from db.services.search_service import SearchConfig, SearchResult


class RecencyDecayType(Enum):
    """Types of recency decay functions."""
    NONE = "none"
    EXPONENTIAL = "exponential"  # score * exp(-age_days / half_life)
    LOGARITHMIC = "logarithmic"  # score * (1 / (1 + log(1 + age_days)))
    LINEAR_WINDOW = "linear_window"  # Full boost for recent, decay for older


@dataclass
class RecencyConfig:
    """Configuration for recency-based score boosting."""
    decay_type: RecencyDecayType = RecencyDecayType.NONE
    half_life_days: float = 180.0  # For exponential decay

    # For linear window decay
    full_boost_days: int = 30  # Full score for last N days
    half_boost_days: int = 90  # 50% boost for N-M days
    quarter_boost_days: int = 365  # 25% boost for M-Y days

    # Boost multiplier (how much to weight recency)
    recency_weight: float = 0.2  # 20% of final score from recency

    def calculate_recency_score(self, created_at: str) -> float:
        """
        Calculate recency score (0-1) based on age of content.

        Args:
            created_at: ISO timestamp of content creation

        Returns:
            Score between 0 and 1 (1 = most recent)
        """
        if self.decay_type == RecencyDecayType.NONE:
            return 1.0

        try:
            # Parse timestamp
            if isinstance(created_at, str):
                # Handle various timestamp formats
                if 'T' in created_at:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = created_at

            now = datetime.now(timezone.utc)
            age_days = (now - dt).days

            if age_days < 0:
                age_days = 0

            if self.decay_type == RecencyDecayType.EXPONENTIAL:
                return math.exp(-age_days / self.half_life_days)

            elif self.decay_type == RecencyDecayType.LOGARITHMIC:
                return 1.0 / (1.0 + math.log(1.0 + age_days))

            elif self.decay_type == RecencyDecayType.LINEAR_WINDOW:
                if age_days <= self.full_boost_days:
                    return 1.0
                elif age_days <= self.half_boost_days:
                    return 0.75
                elif age_days <= self.quarter_boost_days:
                    return 0.5
                else:
                    return 0.25

            return 1.0

        except Exception:
            return 1.0  # Default to no decay on parse error


@dataclass
class SearchStrategy:
    """
    A complete search strategy definition.

    Strategies can customize:
    - SearchConfig (weights, thresholds, limits)
    - Query preprocessing (synonyms, phrase detection)
    - Result post-processing (reranking, boosting)
    - Recency configuration
    """
    name: str
    description: str
    config: SearchConfig
    recency_config: RecencyConfig = field(default_factory=RecencyConfig)

    # Optional processors
    pre_processor: Optional[Callable[[str], str]] = None  # Query preprocessing
    post_processor: Optional[Callable[[List[SearchResult]], List[SearchResult]]] = None  # Result reranking

    def apply_recency_boost(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Apply recency boost to search results.

        Combines the original combined_score with recency score.
        """
        if self.recency_config.decay_type == RecencyDecayType.NONE:
            return results

        weight = self.recency_config.recency_weight

        for result in results:
            recency_score = self.recency_config.calculate_recency_score(result.created_at)
            # Blend: (1 - weight) * original + weight * recency
            result.combined_score = (1 - weight) * result.combined_score + weight * recency_score

        # Re-sort by new combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results


def exact_match_boost_processor(query: str):
    """
    Post-processor that boosts results containing exact query substring.
    Returns a function that can be used as post_processor.
    """
    query_lower = query.lower()

    def processor(results: List[SearchResult]) -> List[SearchResult]:
        for result in results:
            content_lower = result.content.lower()
            if query_lower in content_lower:
                # Boost score by 50% for exact matches
                result.combined_score *= 1.5

        # Re-sort
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results

    return processor


# === STRATEGY DEFINITIONS ===

def create_baseline_strategy() -> SearchStrategy:
    """Current hybrid search with all improvements (phrase matching, exact boost, recency)."""
    return SearchStrategy(
        name="baseline",
        description="Hybrid (40/60) + phrase + exact + recency boost",
        config=SearchConfig(
            vector_weight=0.4,
            fts_weight=0.6,
            vector_similarity_threshold=0.2,
            fts_rank_threshold=0.01,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True,
            enable_phrase_matching=True,
            phrase_boost=2.0,
            enable_exact_substring_boost=True,
            exact_substring_boost=1.5,
            enable_recency_boost=True,
            recency_weight=0.15,
            recency_full_boost_days=30,
            recency_half_boost_days=60,
            recency_quarter_boost_days=180
        )
    )


def create_old_baseline_strategy() -> SearchStrategy:
    """Previous hybrid search (60/40 vector/FTS) for comparison."""
    return SearchStrategy(
        name="old_baseline",
        description="Previous hybrid (60/40) - no improvements",
        config=SearchConfig(
            vector_weight=0.6,
            fts_weight=0.4,
            vector_similarity_threshold=0.2,
            fts_rank_threshold=0.01,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True,
            enable_phrase_matching=False,
            enable_exact_substring_boost=False,
            enable_recency_boost=False
        )
    )


def create_fts_heavy_strategy() -> SearchStrategy:
    """FTS-weighted hybrid (20/80 vector/FTS)."""
    return SearchStrategy(
        name="fts_heavy",
        description="FTS-heavy hybrid (20% vector, 80% FTS)",
        config=SearchConfig(
            vector_weight=0.2,
            fts_weight=0.8,
            vector_similarity_threshold=0.15,
            fts_rank_threshold=0.005,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True
        )
    )


def create_vector_heavy_strategy() -> SearchStrategy:
    """Vector-weighted hybrid (80/20 vector/FTS)."""
    return SearchStrategy(
        name="vector_heavy",
        description="Vector-heavy hybrid (80% vector, 20% FTS)",
        config=SearchConfig(
            vector_weight=0.8,
            fts_weight=0.2,
            vector_similarity_threshold=0.25,
            fts_rank_threshold=0.01,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True
        )
    )


def create_high_recall_strategy() -> SearchStrategy:
    """High recall strategy with lower thresholds and higher limits."""
    return SearchStrategy(
        name="high_recall",
        description="High recall with lower thresholds, more results",
        config=SearchConfig(
            vector_weight=0.5,
            fts_weight=0.5,
            vector_similarity_threshold=0.1,  # Lower threshold
            fts_rank_threshold=0.001,  # Lower threshold
            max_results=100,  # More results
            max_fts_results=200,
            max_vector_results=200,
            enable_query_expansion=True,
            enable_typo_tolerance=True,
            enable_quality_cutoff=False  # Don't cut off results
        )
    )


def create_recency_boost_strategy() -> SearchStrategy:
    """Baseline with exponential recency decay."""
    return SearchStrategy(
        name="recency_boost",
        description="Baseline + exponential recency boost (180-day half-life)",
        config=SearchConfig(
            vector_weight=0.6,
            fts_weight=0.4,
            vector_similarity_threshold=0.2,
            fts_rank_threshold=0.01,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True
        ),
        recency_config=RecencyConfig(
            decay_type=RecencyDecayType.EXPONENTIAL,
            half_life_days=180,
            recency_weight=0.2
        )
    )


def create_recency_strong_strategy() -> SearchStrategy:
    """Strong recency bias with linear window."""
    return SearchStrategy(
        name="recency_strong",
        description="Strong recency bias (linear window, 30% weight)",
        config=SearchConfig(
            vector_weight=0.6,
            fts_weight=0.4,
            vector_similarity_threshold=0.2,
            fts_rank_threshold=0.01,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True
        ),
        recency_config=RecencyConfig(
            decay_type=RecencyDecayType.LINEAR_WINDOW,
            full_boost_days=30,
            half_boost_days=90,
            quarter_boost_days=365,
            recency_weight=0.3
        )
    )


def create_exact_boost_strategy() -> SearchStrategy:
    """Baseline with exact substring match boosting."""
    # Note: post_processor is set dynamically per query
    return SearchStrategy(
        name="exact_boost",
        description="Baseline + boost for exact substring matches",
        config=SearchConfig(
            vector_weight=0.6,
            fts_weight=0.4,
            vector_similarity_threshold=0.2,
            fts_rank_threshold=0.01,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True
        )
    )


def create_recency_exact_strategy() -> SearchStrategy:
    """Combined recency boost and exact match boosting."""
    return SearchStrategy(
        name="recency_exact",
        description="Recency boost + exact match boost",
        config=SearchConfig(
            vector_weight=0.6,
            fts_weight=0.4,
            vector_similarity_threshold=0.2,
            fts_rank_threshold=0.01,
            max_results=50,
            enable_query_expansion=True,
            enable_typo_tolerance=True
        ),
        recency_config=RecencyConfig(
            decay_type=RecencyDecayType.EXPONENTIAL,
            half_life_days=180,
            recency_weight=0.15
        )
    )


def create_fts_only_strategy() -> SearchStrategy:
    """Pure FTS search (no vector)."""
    return SearchStrategy(
        name="fts_only",
        description="Pure full-text search (no vector similarity)",
        config=SearchConfig(
            vector_weight=0.0,
            fts_weight=1.0,
            fts_rank_threshold=0.001,
            max_results=50,
            max_fts_results=200,
            enable_query_expansion=True,
            enable_typo_tolerance=True
        )
    )


def create_vector_only_strategy() -> SearchStrategy:
    """Pure vector search (no FTS)."""
    return SearchStrategy(
        name="vector_only",
        description="Pure semantic vector search (no FTS)",
        config=SearchConfig(
            vector_weight=1.0,
            fts_weight=0.0,
            vector_similarity_threshold=0.15,
            max_results=50,
            max_vector_results=200,
            enable_query_expansion=False,
            enable_typo_tolerance=False
        )
    )


# Registry of all available strategies
STRATEGIES: Dict[str, SearchStrategy] = {}


def register_strategies():
    """Register all built-in strategies."""
    global STRATEGIES
    STRATEGIES = {
        "baseline": create_baseline_strategy(),
        "old_baseline": create_old_baseline_strategy(),
        "fts_heavy": create_fts_heavy_strategy(),
        "vector_heavy": create_vector_heavy_strategy(),
        "high_recall": create_high_recall_strategy(),
        "recency_boost": create_recency_boost_strategy(),
        "recency_strong": create_recency_strong_strategy(),
        "exact_boost": create_exact_boost_strategy(),
        "recency_exact": create_recency_exact_strategy(),
        "fts_only": create_fts_only_strategy(),
        "vector_only": create_vector_only_strategy(),
    }


def get_strategy(name: str) -> Optional[SearchStrategy]:
    """Get a strategy by name."""
    if not STRATEGIES:
        register_strategies()
    return STRATEGIES.get(name)


def list_strategies() -> List[str]:
    """List all available strategy names."""
    if not STRATEGIES:
        register_strategies()
    return list(STRATEGIES.keys())


def get_all_strategies() -> Dict[str, SearchStrategy]:
    """Get all registered strategies."""
    if not STRATEGIES:
        register_strategies()
    return STRATEGIES.copy()


# Initialize strategies on module load
register_strategies()
