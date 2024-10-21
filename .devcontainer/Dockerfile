FROM ghcr.io/nathanvaughn/devcontainers/python:latest

COPY scripts/* scripts/
RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    pulumi_version=$(python scripts/get_pulumi_version.py) \
 && echo "Installing pulumi version $pulumi_version" \
 && curl -fsSL https://get.pulumi.com | sh -s -- --version $pulumi_version
