"""
This script is meant to be executed by pyinfra to configure the server.
"""

import pathlib

from pyinfra.context import host
from pyinfra.facts.server import Command, LinuxDistribution
from pyinfra.operations import apt, files, server, systemd

from scripts import prepare
from scripts.common import DISK_PATH, FILES_DIR, GENERATED_FILES_DIR

SYSTEMD_DIR = pathlib.Path("/etc/systemd/system/")

prepare.main()

# ==============================================
# Format and attach disk
# https://docs.aws.amazon.com/lightsail/latest/userguide/create-and-attach-additional-block-storage-disks-linux-unix.html
# ==============================================

fs = "xfs"
already_formatted = "filesystem" in host.get_fact(Command, f"file -s {DISK_PATH}")
if not already_formatted:
    server.shell(name="Format disk", commands=[f"mkfs -t {fs} {DISK_PATH}"])

files.directory(
    name="Create directory for Factorio data",
    path="/factorio/",
)

# no trailing slash
server.mount(name="Mount the disk", path="/factorio", mounted=True, device=DISK_PATH)

files.line(
    name="Add entry to fstab",
    path="/etc/fstab",
    line=f"/dev/nvme1n1/ /factorio {fs} defaults,nofail 0 2",
)

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
    src="https://download.docker.com/linux/ubuntu/gpg",
    dest="/etc/apt/keyrings/docker.asc",
    mode="444",
    user="root",
    group="root",
)

# Add the Docker repository to sources.list
dpkg_print_architecture = host.get_fact(Command, "dpkg --print-architecture")
codename = host.get_fact(LinuxDistribution)["release_meta"]["CODENAME"]
# fmt: off
apt.repo(
    name="Add Docker repository to sources.list.d",
    filename="docker",
    src=f"deb [arch={dpkg_print_architecture} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {codename} stable",
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
    name="Create the Factorio user",
    user="factorio",
    uid=845,
    ensure_home=False,
    create_home=False,
)

files.put(
    name="Copy Factorio server config",
    src=str(GENERATED_FILES_DIR.joinpath("server-settings.json")),
    dest="/factorio/server/config/server-settings.json",
    user="factorio",
    create_remote_dir=True,
)

# ==============================================
# Setup Services
# ==============================================

# copy files
files.put(
    name="Copy Factorio server service file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_server.service")),
    dest=SYSTEMD_DIR.joinpath("factorio_server.service"),
)

files.put(
    name="Copy Factorio backup service file",
    src=str(FILES_DIR.joinpath("factorio_backup.service")),
    dest=str(SYSTEMD_DIR.joinpath("factorio_backup.service")),
)

files.put(
    name="Copy Factorio backup timer file",
    src=str(FILES_DIR.joinpath("factorio_backup.timer")),
    dest=str(SYSTEMD_DIR.joinpath("factorio_backup.timer")),
)

files.put(
    name="Copy Factorio backup environment file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_backup.env")),
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
