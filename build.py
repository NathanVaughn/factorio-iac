import json
import urllib.request
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR = os.path.join(ROOT_DIR, "inputs")
OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs")

FACTORIO_SERVER_PASSWORD = os.environ["FACTORIO_SERVER_PASSWORD"]
FACTORIO_SERVER_SETTINGS_TEMPLATE = "https://raw.githubusercontent.com/wube/factorio-data/master/server-settings.example.json"

def main():
    with urllib.request.urlopen(FACTORIO_SERVER_SETTINGS_TEMPLATE) as response:
        data = json.loads(response.read().decode())

    # settings we care about
    data["name"] = "Nathan Vaughn's Factorio Server"
    data["description"] = "See above"
    data["visibility"]["public"] = False
    data["game_password"] = FACTORIO_SERVER_PASSWORD

    # write to file
    # needs to end up in /factorio/server/config/server-settings.json
    with open(os.path.join(OUTPUTS_DIR, "server-settings.json"), "w") as fp:
        fp.write(json.dumps(data, indent=4))

if __name__ == "__main__":
    main()