import tomllib

from common import ROOT_DIR

with open(ROOT_DIR.joinpath("poetry.lock"), "rb") as fp:
    data = tomllib.load(fp)

print(next(p["version"] for p in data["package"] if p["name"] == "pulumi"))
