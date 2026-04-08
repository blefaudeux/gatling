# FROM fedora:latest

# RUN dnf install -y podman shadow-utils fuse-overlayfs slirp4netns && \
#     # Create group FIRST, then user
#     groupadd -g ${HOST_GID:-1000} podmanuser && \
#     useradd -u ${HOST_UID:-1000} -g ${HOST_GID:-1000} -m podmanuser && \
#     mkdir -p /home/podmanuser/.config/containers /home/podmanuser/.local/share/containers /run/user/${HOST_UID:-1000} && \
#     chown -R podmanuser:podmanuser /home/podmanuser/.config /home/podmanuser/.local /run/user/${HOST_UID:-1000} && \
#     chmod 700 /run/user/${HOST_UID:-1000} && \
#     echo "podmanuser:100000:65536" > /etc/subuid && \
#     echo "podmanuser:100000:65536" > /etc/subgid && \
#     chmod 644 /etc/subuid /etc/subgid && \
#     chmod u+s /usr/bin/newuidmap /usr/bin/newgidmap

# USER podmanuser
# WORKDIR /home/podmanuser
# ENV XDG_RUNTIME_DIR=/run/user/${HOST_UID:-1000}

FROM rayproject/ray:latest
RUN mkdir -p /tmp/ray