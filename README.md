# tmcf
A builder or compiler for Minecraft datapacks and resource packs.

tmcf has three goals:
1. Reduce repetition and duplication (and writing of micro-scripts)
2. Be as simple as possible
3. Work fully with current mcfunction tooling like [Spyglass](https://github.com/SpyglassMC/Spyglass) (unlike [Bolt](https://github.com/mcbeet/bolt), etc)

Basically, this is for datapack purists who have been turned off by the complexity of Beet, but are sick of having their packs littered with small python files.

🚧(This project is not yet suitable for use, and as such is not yet published on pypi.)🚧

## Quickstart
Run `tmcf init pack` inside an empty directory and follow the steps.

## For Loops
Anywhere within a function file, you may use this syntax:
```mcfunction
#@ for i in range 4
    say i
#@
```
There's no magic here - tmcf just looks at the text between the `#@` comments and performs an unintelligent `.replace()`.

The above example gets compiled into this:
```mcfunction
say 0
say 1
say 2
say 3
```

It's common practice to use a variable name that is a number - this way, Spyglass will have no issues with your file and still provide autocomplete, highlighting, etc:
```mcfunction
#@ for 123123 in range 10
    tp @s ~ ~123123 ~
#@
```
This may look kinda cursed, and admittedly it is, but it's nothing but functional.

## Variables
You can define variables to be used inside your scripts inside the tmcf config.
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
Variables can feature nesting:
```toml
# tmcf.toml
[variables]
foo = [[1,2,3],[4,5,6],[7,8,9]]
```
```mcfunction
#@ for i,j,k in foo
    say ijk
#@
```
This generates the following file:
```mcfunction
say 123
say 456
say 789
```
Note that spaces are not allowed after the commas between variables names because I'm lazy with parsing.
## Enumeration
In addition to `range`, there is one other special case - `enum`. This also behaves exactly like the python function of the same name - `enumerate`.
```mcfunction
#@ for index,str in enum myvar
...
#@
```
## Generate
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
## File Structure
The file structure for a tmcf project looks like a `pack.mcmeta`, `tmcf.toml`, and a `data` and `assets` folders, all next to each other.
tmcf will build your datapack and resource pack from the two folders into the paths specified by the config - usually directly into your Minecraft folders, which the CLI has a handy tool for when you run `tmcf init pack`.
## Json Files
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
The `tmcf` key can be added to any object that is inside an array, and uses the exact same syntax and parsing as the comment inside a function.

In the future, root objects will support the `generate` function inside `tmcf` keys in json files.