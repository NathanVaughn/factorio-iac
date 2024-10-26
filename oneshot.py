import pathlib
import subprocess
import sys

from config import FACTORIO_SERVER_HOSTNAME

ROOT_DIR = pathlib.Path(__file__).parent


subprocess.run(
    [
        sys.executable,
        "wrapper.py",
        "pulumi",
        "update",
        "--stack",
        "prod",
        "--yes",
    ],
    cwd=ROOT_DIR.joinpath("deploy"),
    check=True,
)

# delete old ssh key info. Needed in case the server is redeployed
# don't check the return code because the key might not exist
subprocess.run(["ssh-keygen", "-R", FACTORIO_SERVER_HOSTNAME], check=False)

subprocess.run(
    ["pyinfra", "inventory.py", "configure.py", "-y"],
    cwd=ROOT_DIR.joinpath("configure"),
    check=True,
)
