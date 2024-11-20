import os

# Writes to a file, creating its directories if they are not present
def write(path: str, contents: str):
    os.makedirs(os.path.dirname(os.path.normpath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write(contents)


# A wrapper for a list of strings allowing them to be read one-by-one and passed around
class Consumable:
    strings: list[str]
    index: int
    def __init__(self, l: list[str]):
        self.strings = l
        self.index = 0

    # Returns the item that will be read next
    def preview(self) -> str:
        return self.strings[self.index]

    # Reads the next item
    def consume(self) -> str:
        result = self.strings[self.index]
        self.index += 1
        return result

    # Returns whether there is still more to read or not
    def is_consumable(self) -> bool:
        return self.index < len(self.strings)
