import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent

# local files
TEMPLATES_DIR = ROOT_DIR.joinpath("templates")
FILES_DIR = ROOT_DIR.joinpath("files")
GENERATED_FILES_DIR = FILES_DIR.joinpath("generated")
