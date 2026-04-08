"""Base actor class for container benchmarking."""

import ray
import math
from ray.actor import ActorHandle
from typing import Any
from ray.runtime_env import RuntimeEnv


def create_actor_with_runtime(image: str) -> ActorHandle[Any]:
    """
    Create an actor with a specific container runtime environment.

    Args:
        image: Container image to use for the actor.

    Returns:
        ActorHandle for the created actor.
    """

    # Dynamically create a class with the runtime_env
    @ray.remote(runtime_env=RuntimeEnv(image_uri=image), num_cpus=1)
    class ContainerActor:
        def __init__(self):
            print("initializing actor in a container")
            self.actor_id = id(self)

        def do_work(self, iterations: int = 1000) -> float:
            print("doing work in a container")
            result = math.pi
            for _ in range(iterations):
                result = result**1.0001
            return result

        def get_id(self) -> int:
            print(f"querying actor ID in a container {self.actor_id}")
            return self.actor_id

    return ContainerActor.remote()
