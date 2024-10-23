"""
This script is meant to be executed by pyinfra to configure the server.
"""

import json
import os
import pathlib
import sys
import urllib.request

import dotenv
import jinja2
from pyinfra.context import host
from pyinfra.facts.server import Command, LinuxDistribution
from pyinfra.operations import apt, files, server, systemd

sys.path.append(os.path.join("..", ".."))

from scripts.common import ROOT_DIR

# local files
TEMPLATES_DIR = ROOT_DIR.joinpath("templates")
FILES_DIR = ROOT_DIR.joinpath("files")
GENERATED_FILES_DIR = FILES_DIR.joinpath("generated")

# remote files
DISK_PATH = "/dev/nvme1n1"
SYSTEMD_DIR = pathlib.Path("/etc/systemd/system/")
DATA_DIR = "/factorio"

# local config
CONFIG = dotenv.dotenv_values(ROOT_DIR.joinpath(".env"))


def prepare() -> None:
    # create directories
    GENERATED_FILES_DIR.mkdir(parents=True, exist_ok=True)

    # create server settings
    print("Downloading Factorio server settings template")
    with urllib.request.urlopen(
        "https://raw.githubusercontent.com/wube/factorio-data/master/server-settings.example.json"
    ) as response:
        data = json.loads(response.read().decode())

    # settings we care about
    data["name"] = "Nathan Vaughn's Factorio Server"
    data["description"] = "See above"
    data["visibility"]["public"] = False
    data["game_password"] = CONFIG["FACTORIO_SERVER_PASSWORD"]

    # remove comment fields
    data = {k: v for k, v in data.items() if not k.startswith("_comment")}

    # write to file
    # needs to end up in /factorio/server/config/server-settings.json
    print("Writing Factorio server settings")
    with open(GENERATED_FILES_DIR.joinpath("server-settings.json"), "w") as fp:
        fp.write(json.dumps(data, indent=4))

    # get docker container image
    with open(FILES_DIR.joinpath("Dockerfile"), "r") as fp:
        CONFIG["FACTORIO_IMAGE"] = fp.readline().strip().split("FROM ")[1]

    # template files
    CONFIG["DATA_DIR"] = DATA_DIR
    for template_file in TEMPLATES_DIR.glob("*.j2"):
        # read template
        with open(template_file) as fp:
            template = jinja2.Template(fp.read())

        print(f"Writing {template_file.stem}")

        # write to file
        new_filename = GENERATED_FILES_DIR.joinpath(
            template_file.name.replace(".j2", "")
        )
        with open(new_filename, "w") as fp:
            fp.write(template.render(CONFIG))


prepare()

# ==============================================
# Format and attach disk
# https://docs.aws.amazon.com/lightsail/latest/userguide/create-and-attach-additional-block-storage-disks-linux-unix.html
# ==============================================

fs = "xfs"
print(host.get_fact(Command, f"file -s {DISK_PATH}"))
already_formatted = "filesystem" in host.get_fact(
    Command, f"file -s {DISK_PATH}", _sudo=True
)
if not already_formatted:
    server.shell(name="Format disk", commands=[f"mkfs -t {fs} {DISK_PATH}"])

files.directory(
    name="Create directory for Factorio data",
    path=f"{DATA_DIR}/",
)

# no trailing slash
server.mount(name="Mount the disk", path=DATA_DIR, mounted=True, device=DISK_PATH)

files.line(
    name="Add entry to fstab",
    path="/etc/fstab",
    line=f"/dev/nvme1n1/ {DATA_DIR} {fs} defaults,nofail 0 2",
)

# ==============================================
# Install Docker
# https://docs.docker.com/engine/install/ubuntu/
# ==============================================

# Update package lists before installing dependencies
apt.update(name="Update apt cache", _sudo=True)

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
apt.repo(
    name="Add Docker repository to sources.list.d",
    filename="docker",
    src=f"deb [arch={dpkg_print_architecture} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {codename} stable",
    _sudo=True
)
# fmt: on

# Update package lists again after adding the repository
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
    dest=f"{DATA_DIR}/server/config/server-settings.json",
    user="factorio",
    create_remote_dir=True,
    _sudo=True,
)

# ==============================================
# Setup Services
# ==============================================

# copy files
files.put(
    name="Copy Factorio server service file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_server.service")),
    dest=str(SYSTEMD_DIR.joinpath("factorio_server.service")),
    _sudo=True,
)

files.put(
    name="Copy Factorio backup service file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_backup.service")),
    dest=str(SYSTEMD_DIR.joinpath("factorio_backup.service")),
    _sudo=True,
)

files.put(
    name="Copy Factorio backup timer file",
    src=str(FILES_DIR.joinpath("factorio_backup.timer")),
    dest=str(SYSTEMD_DIR.joinpath("factorio_backup.timer")),
    _sudo=True,
)

files.put(
    name="Copy Factorio backup environment file",
    src=str(GENERATED_FILES_DIR.joinpath("factorio_backup.env")),
    dest=f"{DATA_DIR}/factorio_backup.env",
    _sudo=True,
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
    running=False,
)

systemd.service(
    name="Start Factorio backup timer",
    service="factorio_backup.timer",
    enabled=True,
    running=False,
)
