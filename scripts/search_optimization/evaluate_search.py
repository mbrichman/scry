#!/usr/bin/env python3
"""
Search Strategy Evaluation CLI

Evaluates search strategies against ground truth test cases and produces
comparison reports with standard IR metrics.

Usage:
    # Evaluate single strategy
    python evaluate_search.py --strategy baseline

    # Compare multiple strategies
    python evaluate_search.py --compare baseline,recency_boost,exact_boost

    # Run quick smoke test (first 5 cases)
    python evaluate_search.py --quick

    # Add new test case
    python evaluate_search.py --add-case "query text" --expected-conv-id UUID

    # List available strategies
    python evaluate_search.py --list-strategies
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.services.search_service import SearchService, SearchConfig, SearchResult
from db.services.search_strategies import (
    get_strategy, list_strategies, get_all_strategies,
    SearchStrategy, exact_match_boost_processor
)
from scripts.search_optimization.evaluation_metrics import (
    evaluate_single_case, aggregate_results, format_comparison_table,
    EvaluationResult, AggregateMetrics
)


# Paths
GROUND_TRUTH_PATH = PROJECT_ROOT / "tests" / "search_optimization" / "ground_truth_queries.json"
RESULTS_DIR = PROJECT_ROOT / "search_analysis"


class SearchEvaluator:
    """
    Evaluates search strategies against ground truth test cases.
    """

    def __init__(self, ground_truth_path: Optional[Path] = None):
        self.ground_truth_path = ground_truth_path or GROUND_TRUTH_PATH
        self.test_cases = self._load_ground_truth()
        self.search_service = SearchService()

    def _load_ground_truth(self) -> List[Dict[str, Any]]:
        """Load test cases from ground truth JSON."""
        if not self.ground_truth_path.exists():
            print(f"Warning: Ground truth file not found: {self.ground_truth_path}")
            return []

        with open(self.ground_truth_path, 'r') as f:
            data = json.load(f)

        return data.get('test_cases', [])

    def evaluate_strategy(
        self,
        strategy: SearchStrategy,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        verbose: bool = False
    ) -> Tuple[List[EvaluationResult], AggregateMetrics]:
        """
        Evaluate a strategy against all test cases.

        Args:
            strategy: SearchStrategy to evaluate
            test_cases: Optional subset of test cases (uses all by default)
            verbose: Print progress for each test case

        Returns:
            Tuple of (individual results, aggregate metrics)
        """
        cases = test_cases or self.test_cases

        if not cases:
            print("No test cases to evaluate")
            return [], AggregateMetrics(strategy_name=strategy.name)

        print(f"\nEvaluating strategy: {strategy.name}")
        print(f"  Description: {strategy.description}")
        print(f"  Test cases: {len(cases)}")
        print("-" * 60)

        results = []

        for i, tc in enumerate(cases):
            query = tc['query']

            if verbose:
                print(f"  [{i+1}/{len(cases)}] '{query[:40]}...'", end=" ")

            # Execute search with strategy config
            try:
                search_results, _ = self.search_service.search(
                    query=query,
                    limit=100,  # Get enough results for evaluation
                    config_override=strategy.config,
                    show_all=True  # Don't apply quality cutoff
                )

                # Apply post-processing if defined
                if strategy.name == "exact_boost" or strategy.name == "recency_exact":
                    # Apply exact match boost
                    processor = exact_match_boost_processor(query)
                    search_results = processor(search_results)

                # Apply recency boost if configured
                search_results = strategy.apply_recency_boost(search_results)

                # Extract conversation IDs in ranked order
                retrieved_conv_ids = [r.conversation_id for r in search_results]

                # Evaluate against ground truth
                eval_result = evaluate_single_case(
                    tc,
                    retrieved_conv_ids,
                    k=tc.get('must_appear_in_top_k', 10)
                )
                results.append(eval_result)

                if verbose:
                    status = "HIT" if eval_result.hit_at_k else "MISS"
                    pos = eval_result.first_relevant_position or "-"
                    print(f"[{status}] pos={pos}")

            except Exception as e:
                print(f"  Error evaluating '{query[:30]}': {e}")
                # Add failed result
                results.append(EvaluationResult(
                    test_case_id=tc['id'],
                    query=query,
                    expected_conversations=set(tc.get('expected_conversations', [])),
                    retrieved_conversations=[],
                    k=tc.get('must_appear_in_top_k', 10)
                ))

        # Calculate aggregate metrics
        aggregate = aggregate_results(results, strategy.name, cases)

        print(f"\nResults for {strategy.name}:")
        print(f"  MRR: {aggregate.mrr:.4f}")
        print(f"  Hit Rate@K: {aggregate.hit_rate_at_k:.2%}")
        print(f"  Recall@K: {aggregate.mean_recall_at_k:.4f}")
        print(f"  Precision@K: {aggregate.mean_precision_at_k:.4f}")

        return results, aggregate

    def compare_strategies(
        self,
        strategy_names: List[str],
        verbose: bool = False
    ) -> Dict[str, AggregateMetrics]:
        """
        Compare multiple strategies side-by-side.

        Args:
            strategy_names: List of strategy names to compare
            verbose: Print progress for each test case

        Returns:
            Dict mapping strategy name to aggregate metrics
        """
        all_metrics = {}

        for name in strategy_names:
            strategy = get_strategy(name)
            if not strategy:
                print(f"Warning: Strategy '{name}' not found, skipping")
                continue

            _, metrics = self.evaluate_strategy(strategy, verbose=verbose)
            all_metrics[name] = metrics

        # Print comparison table
        print(format_comparison_table(list(all_metrics.values()), include_breakdown=True))

        return all_metrics

    def run_quick_test(self, n_cases: int = 5) -> Dict[str, AggregateMetrics]:
        """Run quick evaluation on first N test cases."""
        if not self.test_cases:
            print("No test cases available")
            return {}

        subset = self.test_cases[:n_cases]
        print(f"Running quick test with {len(subset)} test cases...")

        # Test key strategies
        strategies = ["baseline", "recency_boost", "exact_boost", "high_recall"]
        all_metrics = {}

        for name in strategies:
            strategy = get_strategy(name)
            if strategy:
                _, metrics = self.evaluate_strategy(strategy, test_cases=subset, verbose=True)
                all_metrics[name] = metrics

        print(format_comparison_table(list(all_metrics.values())))
        return all_metrics

    def add_test_case(
        self,
        query: str,
        expected_conv_id: str,
        description: Optional[str] = None,
        must_appear_in_top_k: int = 10,
        query_type: str = "keyword",
        difficulty: str = "medium"
    ):
        """
        Add a new test case to the ground truth file.

        Args:
            query: Search query
            expected_conv_id: Expected conversation ID
            description: Optional description
            must_appear_in_top_k: K value for evaluation
            query_type: Type of query (keyword, exact_phrase, semantic, natural_language)
            difficulty: Difficulty level (easy, medium, hard)
        """
        # Load existing data
        if self.ground_truth_path.exists():
            with open(self.ground_truth_path, 'r') as f:
                data = json.load(f)
        else:
            data = {
                "metadata": {
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Ground truth test cases for search quality evaluation",
                    "version": "1.0"
                },
                "test_cases": []
            }

        # Generate new ID
        existing_ids = [tc['id'] for tc in data['test_cases']]
        new_num = len(existing_ids) + 1
        new_id = f"tc_{new_num:03d}"
        while new_id in existing_ids:
            new_num += 1
            new_id = f"tc_{new_num:03d}"

        # Create new test case
        new_case = {
            "id": new_id,
            "query": query,
            "description": description or f"Added via CLI on {datetime.now().strftime('%Y-%m-%d')}",
            "expected_conversations": [expected_conv_id],
            "expected_messages": [],
            "must_appear_in_top_k": must_appear_in_top_k,
            "query_type": query_type,
            "difficulty": difficulty
        }

        data['test_cases'].append(new_case)

        # Save
        with open(self.ground_truth_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Added test case {new_id}:")
        print(f"  Query: {query}")
        print(f"  Expected: {expected_conv_id}")
        print(f"  Must appear in top {must_appear_in_top_k}")

        # Reload test cases
        self.test_cases = self._load_ground_truth()

    def save_results(
        self,
        strategy_name: str,
        results: List[EvaluationResult],
        aggregate: AggregateMetrics,
        output_dir: Optional[Path] = None
    ) -> Path:
        """Save evaluation results to JSON file."""
        output_dir = output_dir or RESULTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eval_{strategy_name}_{timestamp}.json"
        filepath = output_dir / filename

        output = {
            "strategy": strategy_name,
            "timestamp": datetime.now().isoformat(),
            "num_test_cases": len(results),
            "aggregate_metrics": aggregate.to_dict(),
            "individual_results": [r.to_dict() for r in results]
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"Results saved to: {filepath}")
        return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate search strategies against ground truth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate baseline strategy
  python evaluate_search.py --strategy baseline

  # Compare multiple strategies
  python evaluate_search.py --compare baseline,recency_boost,exact_boost

  # Quick test (first 5 cases)
  python evaluate_search.py --quick

  # List all strategies
  python evaluate_search.py --list-strategies

  # Add new test case
  python evaluate_search.py --add-case "my query" --expected-conv-id UUID-HERE
        """
    )

    parser.add_argument(
        '--strategy',
        type=str,
        help='Evaluate a single strategy'
    )

    parser.add_argument(
        '--compare',
        type=str,
        help='Compare strategies (comma-separated list)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick test on first 5 test cases'
    )

    parser.add_argument(
        '--list-strategies',
        action='store_true',
        help='List all available strategies'
    )

    parser.add_argument(
        '--add-case',
        type=str,
        metavar='QUERY',
        help='Add a new test case with this query'
    )

    parser.add_argument(
        '--expected-conv-id',
        type=str,
        help='Expected conversation ID for --add-case'
    )

    parser.add_argument(
        '--difficulty',
        type=str,
        default='medium',
        choices=['easy', 'medium', 'hard'],
        help='Difficulty for new test case'
    )

    parser.add_argument(
        '--query-type',
        type=str,
        default='keyword',
        choices=['keyword', 'exact_phrase', 'semantic', 'natural_language'],
        help='Query type for new test case'
    )

    parser.add_argument(
        '--top-k',
        type=int,
        default=10,
        help='Must appear in top K for new test case'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to file'
    )

    args = parser.parse_args()

    # List strategies
    if args.list_strategies:
        print("\nAvailable Search Strategies:")
        print("-" * 60)
        for name, strategy in get_all_strategies().items():
            print(f"  {name:<20} {strategy.description}")
        print()
        return

    # Create evaluator
    evaluator = SearchEvaluator()

    # Add test case
    if args.add_case:
        if not args.expected_conv_id:
            print("Error: --expected-conv-id required with --add-case")
            sys.exit(1)

        evaluator.add_test_case(
            query=args.add_case,
            expected_conv_id=args.expected_conv_id,
            must_appear_in_top_k=args.top_k,
            query_type=args.query_type,
            difficulty=args.difficulty
        )
        return

    # Quick test
    if args.quick:
        evaluator.run_quick_test()
        return

    # Compare strategies
    if args.compare:
        strategy_names = [s.strip() for s in args.compare.split(',')]
        evaluator.compare_strategies(strategy_names, verbose=args.verbose)
        return

    # Evaluate single strategy
    if args.strategy:
        strategy = get_strategy(args.strategy)
        if not strategy:
            print(f"Error: Strategy '{args.strategy}' not found")
            print(f"Available: {', '.join(list_strategies())}")
            sys.exit(1)

        results, aggregate = evaluator.evaluate_strategy(strategy, verbose=args.verbose)

        if args.save:
            evaluator.save_results(args.strategy, results, aggregate)

        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
