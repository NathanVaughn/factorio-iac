import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent
TEMPLATES_DIR = ROOT_DIR.joinpath("templates")
FILES_DIR = ROOT_DIR.joinpath("files")
GENERATED_FILES_DIR = FILES_DIR.joinpath("generated")
DISK_PATH = "/dev/xvdf"

# https://github.com/cloudflare/wrangler-legacy/issues/209#issuecomment-541654484
CLOUDFLARE_ACCOUNT_ID = "57ac323804932b01e44e546ff34ba9a3"
