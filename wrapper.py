# Pulumi config file is completely broken, so this is a workaround
# to run the given command with the contents of the `.env` file passed in

import os
import subprocess
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(THIS_DIR, ".env")


def read_env() -> dict:
    # check if file exists
    if not os.path.isfile(ENV_FILE):
        print("WARNING: .env file not found")
        return {}

    env = {}

    with open(ENV_FILE) as fp:
        for line in fp:
            # skip empty or comment lines
            if line.strip() == "" or line.strip().startswith("#"):
                continue

            # split key and value
            key, value = line.strip().split("=", 1)
            env[key] = value

    if env:
        print(", ".join(list(env.keys())) + " loaded from .env")
    else:
        print("No environment variables loaded from .env")

    return env


def main():  # sourcery skip: dict-assign-update-to-union
    # copy existing environment
    new_env = os.environ.copy()

    # merge with .env file
    env = read_env()
    new_env.update(env)

    # run given command
    cmd = sys.argv[1:]
    print("> " + " ".join(cmd))
    proc = subprocess.run(cmd, env=new_env)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
