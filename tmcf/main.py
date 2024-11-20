import sys
import tomllib
from typing import TypedDict
from os.path import exists

from tmcf.logging import l
from tmcf.command import init
from tmcf.command import build

class ConfigType(TypedDict):
    global_replace: dict
    variables: dict
    assets_out: str
    data_out: str

def main():
    args = sys.argv

    if len(args) > 1 and args[1] == "init":
        if len(args) > 2 and args[2] == "pack":
            init.make_pack_folders()
        return init.init_config()

    # Ensure necessary files exist
    if not exists("./pack.mcmeta"):
        l.fatal("Failed to find pack mcmeta. Run `tmcf init pack` to create.")
    if not exists("./data"):
        l.fatal("Failed to find data directory. Run `tmcf init pack` to create.")
    if not exists("./assets"):
        l.fatal("Failed to find assets directory. Run `tmcf init pack` to create.")
    if not exists("./tmcf.toml"):
        l.fatal("Failed to find `tmcf.toml` config file. Run `tmcf init` to create.")

    config = validate_config()
    build.build_pack(config)

def validate_config() -> ConfigType:
    with open("./tmcf.toml", "rb") as toml:
        config = tomllib.load(toml)
        # Validate config
        if "data_out" not in config: l.fatal("Missing required key 'data_out' in 'tmcf.toml'")
        if "assets_out" not in config: l.fatal("Missing required key 'assets_out' in 'tmcf.toml'")

        if "variables" in config:
            if "range" in config["variables"]:
                l.fatal("Found reserved variable name 'range' in config.")

            for var, val in config["variables"].items():
                if isinstance(val, dict):
                    l.fatal(f"Variable '{var}' in config must be a list, number, or string")

        if "global_replace" in config:
            stripped = config["global_replace"].copy()
            stripped.pop("function", None)
            stripped.pop("json", None)
            config["global_replace"] = {
                "function": {**config["global_replace"].get("function", {}), **stripped},
                "json": {**config["global_replace"].get("json", {}), **stripped}
            }
    return config

if __name__ == '__main__':
    main()