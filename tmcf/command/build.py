import glob
import json
import os
import shutil
from typing import Iterable

from tmcf.main import ConfigType
from tmcf.logging import l, function_ref, generic_ref
from tmcf.utils import write, Consumable

config: ConfigType = None

def build_pack(conf: ConfigType):
    global config
    config = conf

    l.success("Building!")

    out_dp = config["data_out"]
    out_rp = config["assets_out"]

    # Delete previous build
    shutil.rmtree(out_dp, ignore_errors=True)
    shutil.rmtree(out_rp, ignore_errors=True)

    # Create output directories
    os.makedirs(out_dp, exist_ok=True)
    os.makedirs(out_rp, exist_ok=True)

    shutil.copy("./pack.mcmeta", out_dp)
    shutil.copy("./pack.mcmeta", out_rp)

    # Process functions
    functions = glob.glob("./data/**/*.mcfunction", recursive=True)
    for function_path in functions:
        with open(function_path, "r") as f:
            output = ""
            lines = Consumable(f.readlines())

        # Process the lines of the function
        while lines.is_consumable():
            output += handle_line(lines, function_path)

        # Only write to output if function has contents
        if output.strip():
            # Handle global replacements
            for replacee, replacement in config["global_replace"]["function"].items():
                output = output.replace(replacee, replacement)

            write(os.path.join(out_dp, function_path[2:]), output)

    # Process json files
    json_files = glob.glob("./data/**/*.json", recursive=True)
    for json_path in json_files:
        with open(json_path, "r") as f:
            j = json.load(f)

        process_json(j, json_path)
        write(os.path.join(out_dp, json_path[2:]), json.dumps(j, indent = 2))

    l.success("Successfully built!")


def handle_line(lines: Consumable, path: str):
    line = lines.consume().strip()

    if not line.startswith("#@"): return line

    tokens = line.strip().split(" ")

    if not len(tokens) > 1:
        l.fatal(f"Missing token after tmcf comment - expected 'for', 'generate', or 'using'", function_ref(path, lines.index))

    match tokens[1]:
        case "for":
            content, *_ = function_for_loop(tokens, lines, path)
            return "\n".join(content)
        case "generate":
            file_generations(tokens, lines, path)
            return ""
        case "using":
            return using_variable(tokens[1:], lines, path)
        case _ as t:
            l.fatal(f"Unexpected token '{t}' in tmcf comment - expected 'for', 'generate', or 'using'", function_ref(path, lines.index))


def get_variable_from_config(name: str, ref: str):
    if name in config["variables"]:
        return config["variables"][name]
    l.fatal(f"Failed to find variable '{name}' in config.", ref)


def parse_using(tokens: list[str], err_ref: str) -> (list[str], list[object]):
    if len(tokens) != 4:
        l.fatal("Not enough tokens in 'using' block", err_ref)

    variables = tokens[1].split(",")
    if tokens[2] != "as":
        l.fatal(f"Unexpected token '{tokens[2]}' in 'using' block - expected 'as'", err_ref)

    replacements = [get_variable_from_config(token, err_ref) for token in tokens[3].split(",")]
    return variables, replacements

def using_variable(tokens: list[str], lines: Consumable, path: str) -> str:
    variables, replacements = parse_using(tokens, function_ref(path, lines.index))

    if any([isinstance(replacement, dict) or isinstance(replacement, list) for replacement in replacements]):
        l.fatal("Variable used in 'using' block must be a string or number.")

    output: list[str] = []

    while True:
        line = lines.preview()

        # Stop parsing when the closing comment "#@" is reached
        if line.strip() == "#@":
            lines.consume()
            break

        output.append(handle_line(lines, path))

    return bulk_replace("\n".join(output), variables, replacements, function_ref(path, lines.index))


def file_generations(tokens: list[str], lines: Consumable, path: str):
    functions, variables, replacementss = function_for_loop(tokens[2:], lines, path)

    for [function, replacements] in zip(functions, replacementss):
        filename = bulk_replace(tokens[2], variables, replacements)
        if filename == tokens[2]:
            l.fatal(f"Function file names in 'generate' must include a variable from the for loop (cannot create duplicate file names)", function_ref(path, lines.index))

        write(os.path.join(config["data_out"], path[2:], f"../{filename}.mcfunction"), function)

def map_to_nested(li: Iterable):
    return [(i,) for i in li]

def parse_for_loop(tokens: list[str], ref: str) -> (list[str], list):
    if len(tokens) < 4:
        l.fatal(f"Too few tokens in for loop in tmcf comment - expected 'for <variable(s)> in <<list> | 'range' | 'enum'>'", ref)

    if tokens[2] != "in":
        l.fatal(f"Unexpected token '{tokens[2]}' in tmcf comment - expected 'in'", ref)

    variables = tokens[1].split(",")

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

        items = list(enumerate(get_variable_from_config(tokens[4], ref)))

    else:
        items = get_variable_from_config(replacement, ref)
        nested = all([isinstance(i, list) for i in items])

        if any([isinstance(i, list) for i in items]) and not nested:
            l.fatal(f"Variable '{replacement}' contains mixed types.")
        if not nested:
            items = map_to_nested(items)
        if not isinstance(items, list):
            l.fatal(f"Variable '{replacement}' used in for loop is not a list", ref)

    return variables, items

def function_for_loop(tokens: list[str], lines: Consumable, path: str) -> (list[str], list[str], list):
    # File reference of the function, to be used if an error is found
    ref = function_ref(path, lines.index)
    variables, items = parse_for_loop(tokens[1:], ref)
    # Lines of text in the comment "block" defined with #@
    block_lines: list[str] = []

    while True:
        block_line = lines.preview()

        # Stop parsing when the closing comment "#@" is reached
        if block_line.strip() == "#@":
            lines.consume()
            break

        block_lines.append(handle_line(lines, path))

    # Handle blocks that contain commented-out commands in order to not have IDE errors
    if all([line.startswith("#") for line in block_lines]):
        output = "\n".join([line[1:] for line in block_lines])
    else:
        output = "\n".join(block_lines)

    return [bulk_replace(output, variables, item) for item in items], variables, items

def bulk_replace(s: str, replacees: list[str], replacements: list, ref: str = None) -> str:
    # Replaces each instance of a substring in `s` in `replacees` with the corresponding replacement from `replacements`
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
        return

    for [key, value] in object.items():
        if isinstance(value, list) or isinstance(value, dict):
            process_json(value, path, object)

        elif key == "tmcf":
            tokens = value.split(" ")
            if not len(tokens) > 0:
                l.fatal(f"Missing token in 'tmcf' json key - expected 'for', 'generate' or 'using'", generic_ref(path))

            match tokens[0]:
                case "for":
                    if not isinstance(parent, list):
                        l.fatal("For loops in json files can only be used in objects inside arrays", generic_ref(path))

                    parent.remove(object)
                    object.pop("tmcf")

                    variables, items = parse_for_loop(tokens, generic_ref(path))
                    self = json.dumps(object)

                    for [i, replacements] in enumerate(items):
                        try:
                            replaced = json.loads(bulk_replace(self, variables, replacements, generic_ref(path)))
                        except json.JSONDecodeError:
                            print(bulk_replace(json.dumps(self, indent=4), variables, replacements))
                            l.fatal("Json decode error. Output shown above", generic_ref(path))
                            return # keeps pycharm happy
                        # this is cursed but works
                        if i == 0:
                            process_json(replaced, path, object)
                        parent.append(replaced)
                    return
                case "generate":
                    if parent:
                        l.fatal("File generation in json files can only be used in the root object", generic_ref(path))
                    object.pop("tmcf")

                    variables, items = parse_for_loop(tokens[2:], generic_ref(path))
                    process_json(object, path)
                    self = json.dumps(object)

                    for replacements in items:
                        filename = bulk_replace(tokens[1], variables, replacements)
                        write(os.path.join(config["data_out"], path[2:], f"../{filename}.json"), bulk_replace(self, variables, replacements))
                    return
                case "using":
                    variables, replacements = parse_using(tokens, generic_ref(path))

                    parent.remove(object)
                    object.pop("tmcf")
                    self = json.dumps(object)
                    try:
                        parent.append(json.loads(bulk_replace(self, variables, replacements, generic_ref(path))))
                    except json.JSONDecodeError:
                        print(bulk_replace(json.dumps(self, indent=4), variables, replacements))
                        l.fatal("Json decode error. Output shown above", generic_ref(path))
                    return
                case _ as t:
                    l.fatal(f"Unexpected token '{t}' in 'tmcf' json key  - expected 'for', 'generate' or 'using'", generic_ref(path))