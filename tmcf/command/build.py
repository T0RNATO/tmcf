import glob
import json
import os
import shutil
from typing import Iterable

from ..main import ConfigType
from ..logging import l, function_ref, generic_ref
from ..utils import write, Consumable

config: ConfigType = None

def build_pack(conf: ConfigType):
    global config
    config = conf

    l.success("Building!")

    # Prepare output for writing
    out_dp = os.path.join(config["data_out"], "tmcf_build")
    out_rp = os.path.join(config["assets_out"], "tmcf_build")

    shutil.rmtree(out_dp, ignore_errors=True)
    shutil.rmtree(out_rp, ignore_errors=True)

    os.makedirs(out_dp, exist_ok=True)
    os.makedirs(out_rp, exist_ok=True)

    shutil.copy("./pack.mcmeta", out_dp)
    shutil.copy("./pack.mcmeta", out_rp)

    functions = glob.glob("./data/**/*.mcfunction", recursive=True)
    for function_path in functions:
        with open(function_path, "r") as f:
            output = ""
            lines = Consumable(f.readlines())
        while lines.consumable():
            output += handle_line(lines, function_path)
        if output.strip():
            for replacee, replacement in config["global_replace"]["function"].items():
                output = output.replace(replacee, replacement)
            write(os.path.join(out_dp, function_path[2:]), output)

    json_files = glob.glob("./data/**/*.json", recursive=True)
    for json_path in json_files:
        with open(json_path, "r") as f:
            j = json.load(f)
        process_json(j, json_path)
        write(os.path.join(out_dp, json_path[2:]), json.dumps(j, indent = 2))

    l.success("Successfully built!")


def handle_line(lines: Consumable, path: str):
    line = lines.consume()
    if line.startswith("#@"):
        tokens = line.strip().split(" ")
        if len(tokens) > 1:
            match tokens[1]:
                case "for":
                    content, *_ = function_for_loop(tokens, lines, path)
                    return "".join(content)
                case "generate":
                    file_generations(tokens, lines, path)
                    return ""
                case _ as t:
                    l.fatal(f"Unexpected token '{t}' in tmcf comment - expected 'for' or 'generate'", function_ref(path, lines.index))

        l.fatal(f"Missing token after tmcf comment - expected 'for' or 'generate'", function_ref(path, lines.index))

    else: return line


def file_generations(tokens: list[str], lines: Consumable, path: str):
    out_dp = os.path.join(config["data_out"], "tmcf_build")
    functions, variables, replacementss = function_for_loop(tokens[2:], lines, path)

    for [function, replacements] in zip(functions, replacementss):
        filename = bulk_replace(tokens[2], variables, replacements)
        if filename == tokens[2]:
            l.fatal(f"Function file names in 'generate' must include a variable from the for loop (cannot create duplicate file names)", function_ref(path, lines.index))

        write(os.path.join(out_dp, path[2:], f"../{filename}.mcfunction"), function)

def map_to_nested(li: Iterable):
    return [(i,) for i in li]

def parse_for_loop(tokens: list[str], ref: str) -> (list[str], list):
    if len(tokens) < 4:
        l.fatal(f"Too few tokens in for loop in tmcf comment - expected 'for <variable(s)> in <<list> | 'range' | 'enum'>'", ref)

    variables = tokens[1].split(",")
    if tokens[2] != "in":
        l.fatal(f"Unexpected token '{tokens[2]}' in tmcf comment - expected 'in'", ref)

    replacement = tokens[3]
    items = []
    if replacement == "range":
        if len(tokens) != 5:
            l.fatal(f"Incorrect number of tokens for range for loop in tmcf comment - expected 'range <start>:<end>[:<step>]'", ref)
        if tokens[4] in config["variables"]:
            args = config["variables"][tokens[4]]
            if isinstance(args, list):
                items = map_to_nested(range(*args))
            elif isinstance(args, int):
                items = map_to_nested(range(args))
            else:
                l.fatal("Internal error - this is an impossible state.")
        else:
            t = tokens[4].split(":")
            if not all([a.isnumeric() for a in t]):
                l.fatal(f"Invalid arguments '{tokens[4]}' to range for loop in tmcf comment - expected 'range <start>:<end>[:<step>]'", ref)
            items = map_to_nested(range(*[int(a) for a in t]))
    elif replacement == "enum":
        if len(tokens) != 5:
            l.fatal(f"Incorrect number of tokens for enumeration for loop in tmcf comment - expected 'enum <varname>'", ref)
        if tokens[4] in config["variables"]:
            items = list(enumerate(config["variables"][tokens[4]]))
        else:
            l.fatal(f"Failed to find variable '{tokens[4]} in config.'", ref)
    else:
        if replacement not in config["variables"]:
            l.fatal(f"Failed to find variable '{replacement}' used in for loop in config", ref)
        items = config["variables"][replacement]
        nested = all([isinstance(i, list) for i in items])
        if any([isinstance(i, list) for i in items]) and not nested:
            l.fatal(f"Variable '{replacement}' contains mixed types.")
        if not nested:
            items = map_to_nested(items)
        if not isinstance(items, list):
            l.fatal(f"Variable '{replacement}' used in for loop is not a list", ref)
    return variables, items

def function_for_loop(tokens: list[str], lines: Consumable, path: str) -> (list[str], list[str], list):
    ref = function_ref(path, lines.index)
    variables, items = parse_for_loop(tokens[1:], ref)
    block_lines: list[str] = []

    while True:
        block_line = lines.preview()
        if block_line.strip() == "#@":
            lines.consume()
            break
        block_lines.append(handle_line(lines, path))

    if all([line.startswith("#") for line in block_lines]):
        output = "".join([line[1:] for line in block_lines])
    else:
        output = "".join(block_lines)

    return [bulk_replace(output, variables, item) for item in items], variables, items

def bulk_replace(s: str, replacees: list[str], replacements: list, ref: str = None) -> str:
    output = s
    try:
        for [variable_name, value] in zip(replacees, replacements, strict=True):
            output = output.replace(variable_name, str(value))
    except ValueError:
        l.fatal("Mismatch in number of variables and number of items in list", ref)
    return output

def process_json(object: dict | list, path: str, parent: dict | list = None):
    if isinstance(object, list):
        for obj in object:
            if isinstance(obj, list) or isinstance(obj, dict):
                process_json(obj, path, object)
    else:
        for [key, value] in object.items():
            if isinstance(value, list) or isinstance(value, dict):
                process_json(value, path, object)
            elif key == "tmcf":
                tokens = value.split(" ")
                if len(tokens) > 0:
                    match tokens[0]:
                        case "for":
                            if not isinstance(parent, list):
                                l.fatal("For loops in json files can only be used in objects inside arrays", generic_ref(path))
                            parent.remove(object)
                            object.pop("tmcf")
                            variables, items = parse_for_loop(tokens, generic_ref(path))
                            self = json.dumps(object)
                            for [i, item] in enumerate(items):
                                replaced = json.loads(bulk_replace(self, variables, item))
                                # this is cursed but works
                                if i == 0:
                                    process_json(replaced, path, object)
                                parent.append(replaced)
                            return
                        case "generate":
                            # todo
                            return
                        case _ as t:
                            l.fatal(f"Unexpected token '{t}' in 'tmcf' json key  - expected 'for' or 'generate'", generic_ref(path))

                l.fatal(f"Missing token in 'tmcf' json key - expected 'for' or 'generate'", generic_ref(path))
