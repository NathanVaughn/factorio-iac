import json
import pathlib
import urllib.request

import dotenv
import jinja2

ROOT_DIR = pathlib.Path(__file__).parent
TEMPLATES_DIR = ROOT_DIR.joinpath("templates")
FILES_DIR = ROOT_DIR.joinpath("files")
GENERATED_FILES_DIR = FILES_DIR.joinpath("generated")

CONFIG = dotenv.dotenv_values(ROOT_DIR.joinpath(".env"))

FACTORIO_SERVER_SETTINGS_TEMPLATE = "https://raw.githubusercontent.com/wube/factorio-data/master/server-settings.example.json"


def main():
    # create directories
    GENERATED_FILES_DIR.mkdir(parents=True, exist_ok=True)

    # create server settings
    with urllib.request.urlopen(FACTORIO_SERVER_SETTINGS_TEMPLATE) as response:
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
    with open(GENERATED_FILES_DIR.joinpath("server-settings.json"), "w") as fp:
        fp.write(json.dumps(data, indent=4))

    # get docker container image
    with open(FILES_DIR.joinpath("Dockerfile"), "r") as fp:
        CONFIG["FACTORIO_IMAGE"] = fp.readline().strip().split("FROM ")[1]

    # template files
    for template_file in TEMPLATES_DIR.glob("*.j2"):
        # read template
        with open(template_file) as fp:
            template = jinja2.Template(fp.read())

        # write to file
        new_filename = GENERATED_FILES_DIR.joinpath(
            template_file.name.replace(".j2", "")
        )
        with open(new_filename, "w") as fp:
            fp.write(template.render(CONFIG))


if __name__ == "__main__":
    main()
