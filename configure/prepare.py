import json
import urllib.request

import jinja2
from common import FILES_DIR, GENERATED_FILES_DIR, TEMPLATES_DIR

from config import (
    B2_APPLICATION_KEY,
    B2_APPLICATION_KEY_ID,
    B2_BUCKET_PATH,
    DOCKER_PREFIX,
    FACTORIO_SERVER_DIRECTORY,
    FACTORIO_SERVER_PASSWORD,
)


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
    data["game_password"] = FACTORIO_SERVER_PASSWORD

    # remove comment fields
    data = {k: v for k, v in data.items() if not k.startswith("_comment")}

    # write to file
    # needs to end up in /factorio/server/config/server-settings.json
    print("Writing Factorio server settings")
    with open(GENERATED_FILES_DIR.joinpath("server-settings.json"), "w") as fp:
        fp.write(json.dumps(data, indent=4))

    # get docker container image
    with open(FILES_DIR.joinpath("Dockerfile"), "r") as fp:
        factorio_docker_image = fp.readline().strip().split("FROM ")[1]

    config_dict = {
        "FACTORIO_DOCKER_IMAGE": factorio_docker_image,
        "FACTORIO_SERVER_DIRECTORY": FACTORIO_SERVER_DIRECTORY,
        "DOCKER_PREFIX": DOCKER_PREFIX,
        "B2_BUCKET_PATH": B2_BUCKET_PATH,
        "B2_APPLICATION_KEY_ID": B2_APPLICATION_KEY_ID,
        "B2_APPLICATION_KEY": B2_APPLICATION_KEY,
    }

    # template files
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
            fp.write(template.render(config_dict))
