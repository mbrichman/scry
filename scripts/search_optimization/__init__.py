"""
Search Optimization Scripts

Tools for evaluating and improving search quality.
"""

from .evaluation_metrics import (
    EvaluationResult,
    AggregateMetrics,
    reciprocal_rank,
    recall_at_k,
    precision_at_k,
    ndcg_at_k,
    hit_at_k,
    evaluate_single_case,
    aggregate_results,
    format_comparison_table
)

__all__ = [
    'EvaluationResult',
    'AggregateMetrics',
    'reciprocal_rank',
    'recall_at_k',
    'precision_at_k',
    'ndcg_at_k',
    'hit_at_k',
    'evaluate_single_case',
    'aggregate_results',
    'format_comparison_table'
]
