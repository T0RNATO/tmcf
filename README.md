# tmcf
A builder or compiler for Minecraft datapacks and resource packs.

tmcf has three goals:
1. Reduce repetition and duplication (and writing of micro-scripts)
2. Be as simple as possible
3. Work fully with current mcfunction tooling like [Spyglass](https://github.com/SpyglassMC/Spyglass) (unlike [Bolt](https://github.com/mcbeet/bolt), etc)

🚧(This project is not yet suitable for use, and as such is not yet published on pypi.)🚧

## Quickstart
Run `tmcf init pack` inside an empty directory and follow the steps.

## Syntax
Here's an example within a function file:
```mcfunction
say Function start
#@ for i in range 10
    say i
#@
```
There's no magic here - tmcf just looks at the text between the `#@` comments and performs an unintelligent `.replace()`

It's common practice to use a variable name that is a number - this way, Spyglass will have no issues with your file and still provide autocomplete, highlighting, etc:
```mcfunction
#@ for 123123 in range 10
    tp @s ~ ~123123 ~
#@
```
This may look kinda cursed, and admittedly it is, but it's nothing but functional.

tmcf also features variables, defined in the config, among other things
```toml
# tmcf.toml
[variables]
entity_tags = ["foo", "bar", "baz"]
```
```mcfunction
#@ for tagname in entity_tags
    summon item_display ~ ~ ~ {Tags:["tagname"]}
    tellraw @s {"text":"summoned tagname!"}
#@
```
The `for` syntax also has an extension - `generate`.
```toml
[variables]
directions = ["north", "east", "south", "west"]
```
```mcfunction
#@ generate place_dir for dir in directions
    setblock ~ ~ ~ blast_furnace[facing=dir]
#@
```
This expression generates 4 files, named `place_north`, `place_east`, etc.

Additionally, syntax can be nested:
```mcfunction
#@ generate place_dir for dir in directions
    #@ for 42 in range 1:10:2
        setblock ~ ~42 ~ blast_furnace[facing=dir]
    #@
#@
```
The colon syntax in that example just allows you to specify a start and step - (they're just passed to `range()`, lol)

Also note that the indentation isn't necessary, just good practice.

## Config
```toml
# File path to the "datapacks" folder to build into
data_out = './dist/dp'
# File path to the "resourcepacks" folder to build into
assets_out = './dist/rp'

# Variables accessible from within all files
[variables]
 example = [1, 2, 3]

# Globally replaces strings
[global_replace]
 example_string = "replacement"
# Replacement only within function files:
 function.foo = "replacement"
# Replacement only within json files:
 json.foo = "replacement"
```
The file structure for a tmcf project looks like a `pack.mcmeta`, `tmcf.toml`, and a `data` and `assets` folders, all next to each other. tmcf will build your datapack and resource pack from the two folders into the paths specified by the config - usually directly into your Minecraft folders, which the CLI has a handy tool for when you run `tmcf init pack`.

tmcf also has support for json files:
```json
{
    "model": {
        "type": "minecraft:range_dispatch",
        "property": "minecraft:custom_model_data",
        "entries": [
            {
                "tmcf": "for 42 in range 10",
                "threshold": 42,
                "model": {
                    "type": "minecraft:model",
                    "model": "ns:model_42"
                }
            }
        ]
    }
}
```