from os import path, getenv
from pathlib import Path


def get_root_path() -> Path:
    return Path(path.expanduser(getenv("FOXY_GH_ROOT", "~/.foxy-gh-farmer/mainnet"))).resolve()
