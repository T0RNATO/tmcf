import os

def write(path: str, contents: str):
    os.makedirs(os.path.dirname(os.path.normpath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write(contents)


class Consumable:
    strings: list[str]
    index: int
    def __init__(self, l: list[str]):
        self.strings = l
        self.index = 0

    def preview(self) -> str:
        return self.strings[self.index]

    def consume(self) -> str:
        result = self.strings[self.index]
        self.index += 1
        return result

    def consumable(self) -> bool:
        return self.index < len(self.strings)
