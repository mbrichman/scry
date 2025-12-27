"""
Information Retrieval Evaluation Metrics

Standard IR metrics for evaluating search quality:
- Mean Reciprocal Rank (MRR)
- Recall@K
- Precision@K
- NDCG@K
- Hit Rate@K
"""

import math
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class EvaluationResult:
    """Results from evaluating a single test case."""
    test_case_id: str
    query: str
    expected_conversations: Set[str]
    retrieved_conversations: List[str]

    # Core metrics
    reciprocal_rank: float = 0.0
    hit_at_k: bool = False
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    ndcg_at_k: float = 0.0

    # Position info
    first_relevant_position: Optional[int] = None
    k: int = 10

    # Additional info
    total_retrieved: int = 0
    relevant_retrieved: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_case_id': self.test_case_id,
            'query': self.query,
            'expected': list(self.expected_conversations),
            'first_relevant_position': self.first_relevant_position,
            'reciprocal_rank': round(self.reciprocal_rank, 4),
            'hit_at_k': self.hit_at_k,
            'recall_at_k': round(self.recall_at_k, 4),
            'precision_at_k': round(self.precision_at_k, 4),
            'ndcg_at_k': round(self.ndcg_at_k, 4),
            'k': self.k,
            'total_retrieved': self.total_retrieved,
            'relevant_retrieved': self.relevant_retrieved
        }


@dataclass
class AggregateMetrics:
    """Aggregate metrics across all test cases."""
    strategy_name: str
    num_test_cases: int = 0

    # Aggregate metrics
    mrr: float = 0.0  # Mean Reciprocal Rank
    mean_recall_at_k: float = 0.0
    mean_precision_at_k: float = 0.0
    mean_ndcg_at_k: float = 0.0
    hit_rate_at_k: float = 0.0  # Fraction of queries with at least one hit

    # Breakdown by difficulty
    mrr_by_difficulty: Dict[str, float] = field(default_factory=dict)
    hit_rate_by_difficulty: Dict[str, float] = field(default_factory=dict)

    # Breakdown by query type
    mrr_by_query_type: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy': self.strategy_name,
            'num_test_cases': self.num_test_cases,
            'mrr': round(self.mrr, 4),
            'mean_recall_at_k': round(self.mean_recall_at_k, 4),
            'mean_precision_at_k': round(self.mean_precision_at_k, 4),
            'mean_ndcg_at_k': round(self.mean_ndcg_at_k, 4),
            'hit_rate_at_k': round(self.hit_rate_at_k, 4),
            'mrr_by_difficulty': {k: round(v, 4) for k, v in self.mrr_by_difficulty.items()},
            'hit_rate_by_difficulty': {k: round(v, 4) for k, v in self.hit_rate_by_difficulty.items()},
            'mrr_by_query_type': {k: round(v, 4) for k, v in self.mrr_by_query_type.items()}
        }


def reciprocal_rank(results: List[str], expected: Set[str]) -> float:
    """
    Calculate Reciprocal Rank (RR).

    RR = 1 / rank of first relevant result
    Returns 0 if no relevant result is found.

    Args:
        results: List of retrieved item IDs in ranked order
        expected: Set of relevant/expected item IDs

    Returns:
        Reciprocal rank (0.0 to 1.0)
    """
    for i, result in enumerate(results):
        if result in expected:
            return 1.0 / (i + 1)
    return 0.0


def first_relevant_position(results: List[str], expected: Set[str]) -> Optional[int]:
    """
    Find the position of the first relevant result.

    Args:
        results: List of retrieved item IDs in ranked order
        expected: Set of relevant/expected item IDs

    Returns:
        1-indexed position of first relevant result, or None if not found
    """
    for i, result in enumerate(results):
        if result in expected:
            return i + 1
    return None


def hit_at_k(results: List[str], expected: Set[str], k: int) -> bool:
    """
    Check if any relevant result appears in top-k.

    Args:
        results: List of retrieved item IDs in ranked order
        expected: Set of relevant/expected item IDs
        k: Number of top results to consider

    Returns:
        True if at least one relevant result is in top-k
    """
    return any(r in expected for r in results[:k])


def recall_at_k(results: List[str], expected: Set[str], k: int) -> float:
    """
    Calculate Recall@K.

    Recall@K = |relevant ∩ top-k| / |relevant|

    Args:
        results: List of retrieved item IDs in ranked order
        expected: Set of relevant/expected item IDs
        k: Number of top results to consider

    Returns:
        Recall score (0.0 to 1.0)
    """
    if not expected:
        return 1.0  # No relevant items to find

    relevant_in_top_k = sum(1 for r in results[:k] if r in expected)
    return relevant_in_top_k / len(expected)


def precision_at_k(results: List[str], expected: Set[str], k: int) -> float:
    """
    Calculate Precision@K.

    Precision@K = |relevant ∩ top-k| / k

    Args:
        results: List of retrieved item IDs in ranked order
        expected: Set of relevant/expected item IDs
        k: Number of top results to consider

    Returns:
        Precision score (0.0 to 1.0)
    """
    if k == 0:
        return 0.0

    top_k = results[:k]
    relevant_in_top_k = sum(1 for r in top_k if r in expected)
    return relevant_in_top_k / min(k, len(top_k)) if top_k else 0.0


def dcg_at_k(results: List[str], relevance_grades: Dict[str, float], k: int) -> float:
    """
    Calculate Discounted Cumulative Gain at K.

    DCG@K = Σ (2^rel_i - 1) / log2(i + 1) for i = 1 to k

    Args:
        results: List of retrieved item IDs in ranked order
        relevance_grades: Dict mapping item IDs to relevance grades (0-1 or higher)
        k: Number of top results to consider

    Returns:
        DCG score
    """
    dcg = 0.0
    for i, result in enumerate(results[:k]):
        rel = relevance_grades.get(result, 0)
        # Use position i+1 (1-indexed)
        dcg += (2 ** rel - 1) / math.log2(i + 2)  # log2(i+2) because i is 0-indexed
    return dcg


def ndcg_at_k(results: List[str], expected: Set[str], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.

    For binary relevance (item is relevant or not):
    NDCG@K = DCG@K / IDCG@K

    Args:
        results: List of retrieved item IDs in ranked order
        expected: Set of relevant/expected item IDs
        k: Number of top results to consider

    Returns:
        NDCG score (0.0 to 1.0)
    """
    # Binary relevance: 1 if relevant, 0 otherwise
    relevance_grades = {item: 1.0 for item in expected}

    # Calculate DCG
    dcg = dcg_at_k(results, relevance_grades, k)

    # Calculate ideal DCG (all relevant items at top)
    ideal_results = list(expected)[:k] + [''] * max(0, k - len(expected))
    idcg = dcg_at_k(ideal_results, relevance_grades, k)

    if idcg == 0:
        return 0.0

    return dcg / idcg


def evaluate_single_case(
    test_case: Dict[str, Any],
    results: List[str],
    k: int = 10
) -> EvaluationResult:
    """
    Evaluate a single test case against retrieved results.

    Args:
        test_case: Test case dict with 'id', 'query', 'expected_conversations'
        results: List of retrieved conversation IDs in ranked order
        k: Number of top results to consider for @K metrics

    Returns:
        EvaluationResult with all metrics
    """
    expected = set(test_case.get('expected_conversations', []))
    k_override = test_case.get('must_appear_in_top_k', k)

    return EvaluationResult(
        test_case_id=test_case['id'],
        query=test_case['query'],
        expected_conversations=expected,
        retrieved_conversations=results[:k_override],
        reciprocal_rank=reciprocal_rank(results, expected),
        hit_at_k=hit_at_k(results, expected, k_override),
        recall_at_k=recall_at_k(results, expected, k_override),
        precision_at_k=precision_at_k(results, expected, k_override),
        ndcg_at_k=ndcg_at_k(results, expected, k_override),
        first_relevant_position=first_relevant_position(results, expected),
        k=k_override,
        total_retrieved=len(results),
        relevant_retrieved=sum(1 for r in results if r in expected)
    )


def aggregate_results(
    results: List[EvaluationResult],
    strategy_name: str,
    test_cases: Optional[List[Dict[str, Any]]] = None
) -> AggregateMetrics:
    """
    Calculate aggregate metrics across all test case evaluations.

    Args:
        results: List of EvaluationResult objects
        strategy_name: Name of the search strategy
        test_cases: Optional list of test case dicts for difficulty/type breakdown

    Returns:
        AggregateMetrics with mean/aggregate scores
    """
    if not results:
        return AggregateMetrics(strategy_name=strategy_name)

    n = len(results)

    # Build lookup for test case metadata
    case_metadata = {}
    if test_cases:
        for tc in test_cases:
            case_metadata[tc['id']] = {
                'difficulty': tc.get('difficulty', 'unknown'),
                'query_type': tc.get('query_type', 'unknown')
            }

    # Calculate mean metrics
    mrr = sum(r.reciprocal_rank for r in results) / n
    mean_recall = sum(r.recall_at_k for r in results) / n
    mean_precision = sum(r.precision_at_k for r in results) / n
    mean_ndcg = sum(r.ndcg_at_k for r in results) / n
    hit_rate = sum(1 for r in results if r.hit_at_k) / n

    # Calculate breakdown by difficulty
    mrr_by_difficulty = {}
    hit_rate_by_difficulty = {}
    difficulty_counts = {}

    for r in results:
        meta = case_metadata.get(r.test_case_id, {})
        diff = meta.get('difficulty', 'unknown')

        if diff not in difficulty_counts:
            difficulty_counts[diff] = 0
            mrr_by_difficulty[diff] = 0.0
            hit_rate_by_difficulty[diff] = 0.0

        difficulty_counts[diff] += 1
        mrr_by_difficulty[diff] += r.reciprocal_rank
        if r.hit_at_k:
            hit_rate_by_difficulty[diff] += 1

    for diff in difficulty_counts:
        count = difficulty_counts[diff]
        mrr_by_difficulty[diff] /= count
        hit_rate_by_difficulty[diff] /= count

    # Calculate breakdown by query type
    mrr_by_query_type = {}
    query_type_counts = {}

    for r in results:
        meta = case_metadata.get(r.test_case_id, {})
        qtype = meta.get('query_type', 'unknown')

        if qtype not in query_type_counts:
            query_type_counts[qtype] = 0
            mrr_by_query_type[qtype] = 0.0

        query_type_counts[qtype] += 1
        mrr_by_query_type[qtype] += r.reciprocal_rank

    for qtype in query_type_counts:
        mrr_by_query_type[qtype] /= query_type_counts[qtype]

    return AggregateMetrics(
        strategy_name=strategy_name,
        num_test_cases=n,
        mrr=mrr,
        mean_recall_at_k=mean_recall,
        mean_precision_at_k=mean_precision,
        mean_ndcg_at_k=mean_ndcg,
        hit_rate_at_k=hit_rate,
        mrr_by_difficulty=mrr_by_difficulty,
        hit_rate_by_difficulty=hit_rate_by_difficulty,
        mrr_by_query_type=mrr_by_query_type
    )


def format_comparison_table(
    strategy_metrics: List[AggregateMetrics],
    include_breakdown: bool = False
) -> str:
    """
    Format a comparison table of strategy metrics.

    Args:
        strategy_metrics: List of AggregateMetrics for different strategies
        include_breakdown: Whether to include difficulty/type breakdowns

    Returns:
        Formatted table string
    """
    if not strategy_metrics:
        return "No metrics to display"

    # Header
    lines = [
        "",
        "=" * 80,
        "SEARCH STRATEGY COMPARISON",
        "=" * 80,
        "",
        f"{'Strategy':<20} {'MRR':>8} {'Hit@K':>8} {'R@K':>8} {'P@K':>8} {'NDCG':>8}",
        "-" * 80
    ]

    # Sort by MRR descending
    sorted_metrics = sorted(strategy_metrics, key=lambda x: x.mrr, reverse=True)

    for m in sorted_metrics:
        lines.append(
            f"{m.strategy_name:<20} {m.mrr:>8.4f} {m.hit_rate_at_k:>8.2%} "
            f"{m.mean_recall_at_k:>8.4f} {m.mean_precision_at_k:>8.4f} {m.mean_ndcg_at_k:>8.4f}"
        )

    lines.append("-" * 80)
    lines.append("")

    if include_breakdown and sorted_metrics:
        # Best strategy breakdown
        best = sorted_metrics[0]

        lines.append(f"Best Strategy: {best.strategy_name}")
        lines.append("")

        if best.mrr_by_difficulty:
            lines.append("MRR by Difficulty:")
            for diff, mrr in sorted(best.mrr_by_difficulty.items()):
                hit = best.hit_rate_by_difficulty.get(diff, 0)
                lines.append(f"  {diff:<12} MRR: {mrr:.4f}  Hit@K: {hit:.2%}")
            lines.append("")

        if best.mrr_by_query_type:
            lines.append("MRR by Query Type:")
            for qtype, mrr in sorted(best.mrr_by_query_type.items()):
                lines.append(f"  {qtype:<15} MRR: {mrr:.4f}")
            lines.append("")

    return "\n".join(lines)
