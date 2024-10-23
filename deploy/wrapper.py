# Pulumi config file is completely broken, so this is a workaround
# to run the given command with the contents of the `config.py` file passed in

import os
import subprocess
import sys

sys.path.append("..")

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    CLOUDFLARE_API_TOKEN,
    PULUMI_ACCESS_TOKEN,
)

new_env = os.environ.copy()

# merge with .env file
env = {
    "PULUMI_ACCESS_TOKEN": PULUMI_ACCESS_TOKEN,
    "CLOUDFLARE_API_TOKEN": CLOUDFLARE_API_TOKEN,
    "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
    "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
}
new_env.update(env)

# run given command
cmd = sys.argv[1:]
print("> " + " ".join(cmd))
proc = subprocess.run(cmd, env=new_env)
sys.exit(proc.returncode)
