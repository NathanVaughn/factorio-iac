FROM ghcr.io/nathanvaughn/devcontainers/python:latest

COPY uv.lock uv.lock
COPY scripts/* scripts/
RUN pulumi_version=$(python scripts/get_pulumi_version.py) \
 && echo "Installing pulumi version $pulumi_version" \
 && curl -fsSL https://get.pulumi.com | sh -s -- --version $pulumi_version \
 && rm uv.lock