import json
import os
from os.path import join

from tmcf.cli import prompt, choose_option
from tmcf.logging import l


def make_pack_folders():
    # Create a datapack template with a namespace, pack.mcmeta, and tick & load functions.
    prompt("Namespace")
    namespace = input()
    with open("pack.mcmeta", "w") as mcmeta:
        json.dump({
            "pack": {
                "pack_format": 59,
                "description": ""
            }
        }, mcmeta, indent=4)

    os.makedirs("./data/minecraft/tags/function", exist_ok=True)
    os.makedirs(f"./data/{namespace}/function", exist_ok=True)
    os.makedirs("./assets/minecraft", exist_ok=True)
    os.makedirs(f"./assets/{namespace}", exist_ok=True)

    with open("./data/minecraft/tags/function/tick.json", "w") as j:
        json.dump({ "values": [
            f"ss:tick"
        ]}, j, indent = 4)

    with open("./data/minecraft/tags/function/load.json", "w") as j:
        json.dump({ "values": [
            f"ss:load"
        ]}, j, indent = 4)

    open(f"./data/{namespace}/function/tick.mcfunction", "a").close()
    open(f"./data/{namespace}/function/load.mcfunction", "a").close()

    l.success("Successfully created pack folders and template")


def init_config():
    prismpath = os.path.expandvars("%appdata%/PrismLauncher")
    vanillapath = os.path.expandvars("%appdata%/.minecraft")

    datapack_path = "./dist/"
    resource_pack_path = "./dist/"

    possible_rp_path = None
    saves_path = None
    saves = None

    config = ""

    # Automatically detect minecraft installations and ask which world to build to
    if os.path.exists(prismpath):
        instances = os.listdir(join(prismpath, "instances"))
        choice = choose_option("Choose an instance to build the datapack to", instances)
        if choice.isnumeric():
            mc_path = join(prismpath, "instances", instances[int(choice)], ".minecraft")
            saves_path = join(mc_path, "saves")
            possible_rp_path = join(mc_path, "resourcepacks")
            saves = os.listdir(saves_path)
        else:
            l.warn("No datapack build path specified, defaulting.")

    elif os.path.exists(vanillapath):
        saves_path = join(vanillapath, "saves")
        possible_rp_path = join(vanillapath, "resourcepacks")
        saves = os.listdir(saves_path)

    if saves and len(saves):
        save = choose_option("Choose a save to build the datapack to", saves)
        if save.isnumeric():
            datapack_path = join(saves_path, saves[int(save)], "datapacks")
            config += f"data_output = {datapack_path}\n"
        else:
            l.warn("No datapack build path specified, defaulting.")
    else:
        l.warn("No minecraft installation found on computer. Defaulting datapack build path.")

    if possible_rp_path:
        prompt(f"Use {possible_rp_path} to build the resource pack to? (y/n)")
        if input() == "y":
            resource_pack_path = possible_rp_path
        else:
            l.warn("No resource pack build path specified, defaulting.")

    config = f"""
# File path to the "datapacks" folder to build into
data_out = '{datapack_path}'
# File path to the "resourcepacks" folder to build into
assets_out = '{resource_pack_path}'

# Variables accessible from within all files
[variables]
 example = [1, 2, 3]

# Globally replaces text. Good for config values. Beware footguns!
[global_replace]
 example_string = "replacement"
# Replacement only within function files:
 function.string = "replacement"
# Replacement only within json files:
 json.string = "replacement"
"""
    with open("./tmcf.toml", "w") as f:
        f.write(config)

    l.success("Successfully created `tmcf.toml`")
