"""
This script is meant to be executed by pyinfra to configure the server.
"""

import sys

from pyinfra.context import host
from pyinfra.facts.server import Command, LinuxDistribution
from pyinfra.operations import apt, files, server, systemd

sys.path.append("..")

from common import FILES_DIR, GENERATED_FILES_DIR
from prepare import prepare

from config import FACTORIO_SERVER_DIRECTORY

prepare()


DISK_PATH = "/dev/nvme1n1"
SYSTEMD_DIR = "/etc/systemd/system"

# ==============================================
# Format and attach disk
# https://docs.aws.amazon.com/lightsail/latest/userguide/create-and-attach-additional-block-storage-disks-linux-unix.html
# ==============================================

fs = "xfs"
print(host.get_fact(Command, f"sudo file -s {DISK_PATH}"))
already_formatted = "filesystem" in host.get_fact(Command, f"sudo file -s {DISK_PATH}")
if not already_formatted:
    server.shell(name="Format disk", commands=[f"mkfs -t {fs} {DISK_PATH}"], _sudo=True)

files.directory(
    name="Create directory for Factorio data",
    path=f"{FACTORIO_SERVER_DIRECTORY}/",
    _sudo=True,
)

# no trailing slash
server.mount(
    name="Mount the disk",
    path=FACTORIO_SERVER_DIRECTORY,
    mounted=True,
    device=DISK_PATH,
    _sudo=True,
)

files.line(
    name="Add entry to fstab",
    path="/etc/fstab",
    line=f"{DISK_PATH} {FACTORIO_SERVER_DIRECTORY} {fs} defaults,nofail 0 2",
    _sudo=True,
)

# ==============================================
# Install Docker
# https://docs.docker.com/engine/install/ubuntu/
# ==============================================

# Update package lists before installing dependencies
apt.update(name="Update apt cache", _sudo=True)
apt.upgrade(name="Upgrade packages", auto_remove=True, _sudo=True)

# Install dependencies required for adding the Docker repository
apt.packages(
    name="Install ca-certificates and curl",
    packages=["ca-certificates", "curl"],
    _sudo=True,
)

# Create the directory for the Docker GPG key
files.directory(
    name="Create directory for Docker GPG key",
    path="/etc/apt/keyrings",
    mode="755",
    user="root",
    group="root",
    _sudo=True,
)

# Download the Docker GPG key
files.download(
    name="Download Docker GPG key",
    src="https://download.docker.com/linux/ubuntu/gpg",
    dest="/etc/apt/keyrings/docker.asc",
    mode="444",
    user="root",
    group="root",
    _sudo=True,
)

# Add the Docker repository to sources.list
dpkg_print_architecture = host.get_fact(Command, "dpkg --print-architecture")
codename = host.get_fact(LinuxDistribution)["release_meta"]["CODENAME"]
# fmt: off
docker_repo = apt.repo(
    name="Add Docker repository to sources.list.d",
    filename="docker",
    src=f"deb [arch={dpkg_print_architecture} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {codename} stable",
    _sudo=True
)
# fmt: on

# Update package lists again after adding the repository
if docker_repo.changed:
    apt.update(name="Update apt cache (after adding Docker repository)", _sudo=True)

# Install Docker
apt.packages(
    name="Install Docker",
    packages=["docker-ce", "docker-ce-cli", "containerd.io"],
    _sudo=True,
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
    _sudo=True,
)

files.put(
    name="Copy Factorio server config",
    src=str(GENERATED_FILES_DIR.joinpath("server-settings.json")),
    dest=f"{FACTORIO_SERVER_DIRECTORY}/server/config/server-settings.json",
    user="factorio",
    create_remote_dir=True,
    _sudo=True,
)

# ==============================================
# Setup Services
# ==============================================

# copy files
server_service = files.put(
    name="Copy Factorio server service file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_server.service")),
    dest=f"{SYSTEMD_DIR}/factorio_server.service",
    _sudo=True,
)

backup_service = files.put(
    name="Copy Factorio backup service file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_backup.service")),
    dest=f"{SYSTEMD_DIR}/factorio_backup.service",
    _sudo=True,
)

backup_timer = files.put(
    name="Copy Factorio backup timer file",
    src=str(FILES_DIR.joinpath("factorio_backup.timer")),
    dest=f"{SYSTEMD_DIR}/factorio_backup.timer",
    _sudo=True,
)

files.put(
    name="Copy Factorio backup environment file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_backup.env")),
    dest=f"{FACTORIO_SERVER_DIRECTORY}/factorio_backup.env",
    _sudo=True,
)

# start services
systemd.service(
    name="Start Factorio server service",
    service="factorio_server.service",
    enabled=True,
    running=True,
    restarted=server_service.changed,
    daemon_reload=server_service.changed,
    _sudo=True,
)

systemd.service(
    name="Start Factorio backup service",
    service="factorio_backup.service",
    enabled=True,
    daemon_reload=backup_service.changed,
    _sudo=True,
)

systemd.service(
    name="Start Factorio backup timer",
    service="factorio_backup.timer",
    enabled=True,
    running=True,
    daemon_reload=backup_timer.changed,
    _sudo=True,
)
