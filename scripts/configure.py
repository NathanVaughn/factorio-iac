"""
This script is meant to be executed by pyinfra to configure the server.
"""

import os

import prepare
from common import FILES_DIR, GENERATED_FILES_DIR
from pyinfra.operations import apt, files, server, systemd

SYSTEMD_DIR = "/etc/systemd/system/"

prepare.main()

# ==============================================
# Install Docker
# https://docs.docker.com/engine/install/ubuntu/
# ==============================================

# Update package lists before installing dependencies
apt.update(name="Update apt cache")

# Install dependencies required for adding the Docker repository
apt.packages(
    name="Install ca-certificates and curl",
    packages=["ca-certificates", "curl"],
)

# Create the directory for the Docker GPG key
files.directory(
    name="Create directory for Docker GPG key",
    path="/etc/apt/keyrings",
    mode="755",
    user="root",
    group="root",
)

# Download the Docker GPG key
files.download(
    name="Download Docker GPG key",
    url="https://download.docker.com/linux/ubuntu/gpg",
    dest="/etc/apt/keyrings/docker.asc",
    mode="444",
    user="root",
    group="root",
)

# Add the Docker repository to sources.list
dpkg_print_architecture = server.shell(
    name="Run dpkg --print-architecture",
    commands=["dpkg --print-architecture"],
)
ubuntu_codename = server.shell(
    name="Get Ubuntu codename",
    commands=["cat /etc/os-release | grep UBUNTU_CODENAME | cut -d = -f 2"],
)
# fmt: off
apt.repo(
    name="Add Docker repository to sources.list",
    filename="docker",
    url=f"deb [arch={dpkg_print_architecture.stdout} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {ubuntu_codename.stdout} stable",
)
# fmt: on

# Update package lists again after adding the repository
apt.update(name="Update apt cache (after adding Docker repository)")

# Install Docker
apt.packages(
    name="Install Docker",
    packages=["docker-ce", "docker-ce-cli", "containerd.io"],
)


# ==============================================
# Setup Files
# https://github.com/factoriotools/factorio-docker?tab=readme-ov-file#volumes
# ==============================================

server.user(
    # name="Create the Factorio user",
    user="factorio",
    uid=845,
    ensure_home=False,
    create_home=False,
)

files.put(
    name="Copy Factorio server config",
    src=os.path.join(GENERATED_FILES_DIR, "server-settings.json"),
    dest="/factorio/data/config/server-settings.json",
    user="factorio",
    create_remote_dir=True,
)

# ==============================================
# Setup Services
# ==============================================

# copy files
files.put(
    name="Copy Factorio server service file",
    src=os.path.join(GENERATED_FILES_DIR, "factorio_server.service"),
    dest=os.path.join(SYSTEMD_DIR, "factorio_server.service"),
)

files.put(
    name="Copy Factorio backup service file",
    src=os.path.join(FILES_DIR, "factorio_backup.service"),
    dest=os.path.join(SYSTEMD_DIR, "factorio_backup.service"),
)

files.put(
    name="Copy Factorio backup timer file",
    src=os.path.join(FILES_DIR, "factorio_backup.timer"),
    dest=os.path.join(SYSTEMD_DIR, "factorio_backup.timer"),
)

files.put(
    name="Copy Factorio backup environment file",
    src=os.path.join(GENERATED_FILES_DIR, "factorio_backup.env"),
    dest="/factorio/factorio_backup.env",
)

# start services
systemd.service(
    name="Start Factorio server service",
    service="factorio_server.service",
    running=True,
    enabled=True,
)

systemd.service(
    name="Start Factorio backup service",
    service="factorio_backup.service",
    enabled=True,
)

systemd.service(
    name="Start Factorio backup timer", service="factorio_backup.timer", enabled=True
)
