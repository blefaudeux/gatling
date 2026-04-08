## High level 
The goal of the current repo is to make it possible to benchmark ray as a local service-in-a-container broker. 

## Diving in
We want to have:
- a main which 
  - starts a ray cluster, 
  - takes some settings (what kind of image to use for instance), 
  - and runs the benchmark
- a base actor class, which 
  - will run some dummy (irrelevant) load inside
  - is self contained for now, ie: not using shared resources


## More details and requirements
We want the actors to be created with ray's "runtime_env" option, in which we pass in the container which should be used to start the actor. 
Podman will be used by ray to handle this, we will make sure that it's handled by the system.

This is all local for now, we're trying to find what the limits of the machine and ray are. We're always spinning the same container for a start, but will eventually benchmark spinning up different containers. 

What do we want to benchmark ?
- container creation time
- how many containers can be alive concurrently
- container deletion time

What image shall we use for a start ?
- let's use python:3.13-slime


## Agent behavior
Let the user handle the source control
Let the user handle the initial software stack, let's assume that the repo runs in a container which has ray and podman already installed
