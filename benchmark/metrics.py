"""Benchmark metrics collection for Ray container performance testing."""

from socket import timeout
import time
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import ray

from benchmark.actor import create_actor_with_runtime


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    name: str
    total_time: float
    per_item_time: float
    count: int
    success: bool
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConcurrencyResult:
    """Container for concurrency benchmark results."""

    max_successful: int
    first_failure: Optional[int] = None
    error_message: Optional[str] = None
    times: List[float] = field(default_factory=list)


def measure_creation_time(image: str, num_actors: int) -> BenchmarkResult:
    """
    Measure the time to create N actors with the specified container image.

    Args:
        image: Container image to use for actors.
        num_actors: Number of actors to create.

    Returns:
        BenchmarkResult with timing information.
    """
    actors: list[ray.actor.ActorHandle[Any]] = []
    start_time = time.time()

    try:
        for _ in range(num_actors):
            print(f"Requesting actor creation with image {image}")
            actors.append(create_actor_with_runtime(image))

        # Wait for all actors to be ready
        print("Waiting for actors to be ready")
        results = ray.get([actor.get_id.remote() for actor in actors], timeout=60)
        if not all(results):  # Check if any actor failed to start
            raise Exception("Some actors failed to start")

        end_time = time.time()
        total_time = end_time - start_time
        per_actor_time = total_time / num_actors if num_actors > 0 else 0

        return BenchmarkResult(
            name="container_creation",
            total_time=total_time,
            per_item_time=per_actor_time,
            count=num_actors,
            success=True,
            details={"actors_created": num_actors, "image": image},
        )
    except Exception as e:
        end_time = time.time()
        return BenchmarkResult(
            name="container_creation",
            total_time=end_time - start_time,
            per_item_time=0,
            count=len(actors),
            success=False,
            error=str(e),
            details={"actors_created": len(actors), "image": image},
        )
    finally:
        # Cleanup actors
        for actor in actors:
            try:
                ray.kill(actor)
            except:
                pass


def measure_concurrency(image: str, max_actors: int) -> ConcurrencyResult:
    """
    Measure how many containers can be alive concurrently.

    Uses exponential backoff to find the maximum number of concurrent actors.

    Args:
        image: Container image to use for actors.
        max_actors: Maximum number of actors to attempt.

    Returns:
        ConcurrencyResult with maximum successful concurrent actors.
    """
    actors = []
    times = []

    # Start with 1 actor and double until we hit max or fail
    current_count = 1
    max_successful = 0
    first_failure = None
    error_message = None

    while current_count <= max_actors:
        start_time = time.time()

        try:
            # Create current_count actors
            new_actors = []
            for _ in range(current_count - len(actors)):
                actor = create_actor_with_runtime(image)
                new_actors.append(actor)

            # Wait for all to be ready
            all_actors = actors + new_actors
            ray.get([a.get_id.remote() for a in all_actors])

            end_time = time.time()
            times.append(end_time - start_time)

            actors = all_actors
            max_successful = current_count
            current_count *= 2

        except Exception as e:
            first_failure = current_count
            error_message = str(e)
            break

    # Cleanup
    for actor in actors:
        try:
            ray.kill(actor)
        except:
            pass

    return ConcurrencyResult(
        max_successful=max_successful, first_failure=first_failure, error_message=error_message, times=times
    )


def measure_teardown_time(actors: List[ray.actor.ActorHandle]) -> BenchmarkResult:
    """
    Measure the time to teardown a list of actors.

    Args:
        actors: List of actor handles to teardown.

    Returns:
        BenchmarkResult with timing information.
    """
    start_time = time.time()

    try:
        for actor in actors:
            ray.kill(actor)

        end_time = time.time()
        total_time = end_time - start_time
        per_actor_time = total_time / len(actors) if len(actors) > 0 else 0

        return BenchmarkResult(
            name="container_teardown",
            total_time=total_time,
            per_item_time=per_actor_time,
            count=len(actors),
            success=True,
            details={"actors_removed": len(actors)},
        )
    except Exception as e:
        end_time = time.time()
        return BenchmarkResult(
            name="container_teardown",
            total_time=end_time - start_time,
            per_item_time=0,
            count=len(actors),
            success=False,
            error=str(e),
            details={"actors_removed": 0},
        )


def run_creation_benchmark(image: str, num_actors: int) -> BenchmarkResult:
    """
    Run the container creation benchmark.

    Args:
        image: Container image to use.
        num_actors: Number of actors to create.

    Returns:
        BenchmarkResult with creation timing.
    """
    return measure_creation_time(image, num_actors)


def run_concurrency_benchmark(image: str, max_actors: int) -> ConcurrencyResult:
    """
    Run the concurrency benchmark.

    Args:
        image: Container image to use.
        max_actors: Maximum actors to attempt.

    Returns:
        ConcurrencyResult with maximum concurrent actors.
    """
    return measure_concurrency(image, max_actors)


def run_teardown_benchmark(image: str, num_actors: int) -> BenchmarkResult:
    """
    Run the teardown benchmark.

    Args:
        image: Container image to use.
        num_actors: Number of actors to create and then teardown.

    Returns:
        BenchmarkResult with teardown timing.
    """
    # First create the actors
    actors = []
    try:
        for _ in range(num_actors):
            actor = create_actor_with_runtime(image)
            actors.append(actor)

        ray.get([a.get_id.remote() for a in actors])
        return measure_teardown_time(actors)
    except Exception as e:
        # Cleanup on failure
        for actor in actors:
            try:
                ray.kill(actor)
            except:
                pass
        return BenchmarkResult(
            name="container_teardown",
            total_time=0,
            per_item_time=0,
            count=0,
            success=False,
            error=f"Failed to create actors: {str(e)}",
        )


def format_results(results: Dict[str, Any]) -> str:
    """
    Format benchmark results for output.

    Args:
        results: Dictionary of benchmark results.

    Returns:
        Formatted string representation.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Ray Container Benchmark Results")
    lines.append("=" * 60)

    for benchmark_name, result in results.items():
        lines.append(f"\n{benchmark_name}:")
        lines.append("-" * 40)

        if isinstance(result, BenchmarkResult):
            lines.append(f"  Status: {'SUCCESS' if result.success else 'FAILED'}")
            lines.append(f"  Total Time: {result.total_time:.4f}s")
            lines.append(f"  Per Item Time: {result.per_item_time:.4f}s")
            lines.append(f"  Count: {result.count}")
            if result.error:
                lines.append(f"  Error: {result.error}")
            if result.details:
                lines.append(f"  Details: {result.details}")

        elif isinstance(result, ConcurrencyResult):
            lines.append(f"  Max Successful: {result.max_successful}")
            if result.first_failure:
                lines.append(f"  First Failure at: {result.first_failure}")
            if result.error_message:
                lines.append(f"  Error: {result.error_message}")
            if result.times:
                avg_time = sum(result.times) / len(result.times)
                lines.append(f"  Avg Creation Time: {avg_time:.4f}s")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
