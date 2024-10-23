import pathlib

import tomllib

ROOT_DIR = pathlib.Path(__file__).parent.parent

with open(ROOT_DIR.joinpath("uv.lock"), "rb") as fp:
    data = tomllib.load(fp)

print(next(p["version"] for p in data["package"] if p["name"] == "pulumi"))
