#!/usr/bin/env python
"""Main entry point for Ray container benchmarking tool."""

from argparse import Namespace


import argparse
import sys
import json
from typing import Any

from benchmark.cluster import start_cluster, stop_cluster, get_cluster_status
from benchmark.metrics import (
    run_creation_benchmark,
    run_concurrency_benchmark,
    run_teardown_benchmark,
    format_results,
    BenchmarkResult,
    ConcurrencyResult,
)


def parse_args() -> Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Benchmark Ray container performance with Podman")

    _ = parser.add_argument(
        "--image",
        type=str,
        default="rayproject/ray:latest",
        help="Container image to use for actors (default: python:3.13-slim)",
    )

    _ = parser.add_argument(
        "--benchmark-type",
        type=str,
        choices=["creation", "concurrency", "teardown", "all"],
        default="all",
        help="Type of benchmark to run (default: all)",
    )

    _ = parser.add_argument(
        "--output", type=str, default="stdout", help="Output destination: stdout or filename (default: stdout)"
    )

    _ = parser.add_argument(
        "--num-actors", type=int, default=5, help="Number of actors for creation/teardown benchmarks (default: 5)"
    )

    _ = parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    return parser.parse_args()


def run_benchmarks(args: Namespace) -> dict[str, Any]:
    """
    Run the selected benchmarks.

    Args:
        args: Parsed command line arguments.

    Returns:
        dictionary of benchmark results.
    """
    results = {}

    benchmark_types = {
        "creation": args.benchmark_type in ["creation", "all"],
        "concurrency": args.benchmark_type in ["concurrency", "all"],
        "teardown": args.benchmark_type in ["teardown", "all"],
    }

    # Run creation benchmark
    if benchmark_types["creation"]:
        print(f"Running creation benchmark with {args.num_actors} actors...")
        results["creation"] = run_creation_benchmark(args.image, args.num_actors)
        print(f"  Creation benchmark completed: {results['creation']}")

    # Run concurrency benchmark
    if benchmark_types["concurrency"]:
        print(f"Running concurrency benchmark with max {args.num_actors} actors...")
        results["concurrency"] = run_concurrency_benchmark(args.image, args.num_actors)
        print(f"  Concurrency benchmark completed: {results['concurrency']}")

    # Run teardown benchmark
    if benchmark_types["teardown"]:
        print(f"Running teardown benchmark with {args.num_actors} actors...")
        results["teardown"] = run_teardown_benchmark(args.image, args.num_actors)
        print(f"  Teardown benchmark completed: {results['teardown']}")

    return results


def output_results(results: dict[str, Any], args) -> None:
    """
    Output benchmark results.

    Args:
        results: dictionary of benchmark results.
        args: Parsed command line arguments.
    """
    if args.json:
        # Convert dataclass instances to dicts for JSON serialization
        json_results = {}
        for name, result in results.items():
            if isinstance(result, BenchmarkResult):
                json_results[name] = {
                    "name": result.name,
                    "total_time": result.total_time,
                    "per_item_time": result.per_item_time,
                    "count": result.count,
                    "success": result.success,
                    "error": result.error,
                    "details": result.details,
                }
            elif isinstance(result, ConcurrencyResult):
                json_results[name] = {
                    "max_successful": result.max_successful,
                    "first_failure": result.first_failure,
                    "error_message": result.error_message,
                    "times": result.times,
                }

        output = json.dumps(json_results, indent=2)
    else:
        output = format_results(results)

    if args.output == "stdout":
        print(output)
    else:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results written to {args.output}")


def main():
    """Main entry point."""
    args = parse_args()

    print(f"Starting Ray container benchmark")
    print(f"  Image: {args.image}")
    print(f"  Benchmark type: {args.benchmark_type}")
    print(f"  Num actors: {args.num_actors}")

    # Check if Podman is available
    import subprocess

    try:
        subprocess.run(["podman", "--version"], capture_output=True, check=True)
        print("  Podman: available")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  ERROR: Podman not available: {e}")
        sys.exit(1)

    # Start Ray cluster
    print("Starting Ray cluster...")
    try:
        start_cluster()
        print("Ray cluster started successfully")

        # Run benchmarks
        results = run_benchmarks(args)

        # Output results
        output_results(results, args)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Stop Ray cluster
        print("Stopping Ray cluster...")
        stop_cluster()
        print("Ray cluster stopped")


if __name__ == "__main__":
    main()
