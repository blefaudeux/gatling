# quick notes

## Build with host UID/GID

podman build --build-arg HOST_UID=$(id -u) --build-arg HOST_GID=$(id -g) -t rootless-podman .

##  Run with --userns=host (critical for nested user namespaces)

podman run -it --rm --userns=keep-id -v /var/lib/containers:/var/lib/containers rootless-podman

## Some useful issues listed by anyscale

https://docs.ray.io/en/latest/serve/advanced-guides/multi-app-container.html#compatibility-with-other-runtime-environment-fields

## login podman to ghcr.io

echo $TOKEN | podman login ghcr.io -u $USERNAME --password-stdin