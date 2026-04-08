"""Ray cluster management for container benchmarking."""

import ray
import os


def start_cluster() -> None:
    """
    Initialize a local Ray cluster with Podman as container runtime.

    Args:
        use_container_runtime: If True, configure Ray to use Podman for containers.
    """
    # Set environment variable to use Podman
    # os.environ["RAY_container_runtime"] = "podman"

    ray.init(ignore_reinit_error=True, log_to_driver=True, logging_level="DEBUG")


def stop_cluster() -> None:
    """Shutdown the Ray cluster."""
    ray.shutdown()


def get_cluster_status() -> dict:
    """
    Get Ray cluster status.

    Returns:
        Dictionary with cluster status information.
    """
    try:
        return {
            "initialized": ray.is_initialized(),
            "nodes": ray.nodes() if ray.is_initialized() else [],
            "resources": ray.available_resources() if ray.is_initialized() else {},
        }
    except Exception as e:
        return {"error": str(e)}
