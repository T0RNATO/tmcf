import os
import sys

# Class for printing colours, and it somehow also turned into a logging handler too (oops)
class Logging:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, s: str, *codes):
        return "".join(codes) + s + self.RESET

    def print(self, s, *codes):
        print(self.format(s, *codes))

    def print_e(self, s, *codes):
        print(self.format(s, *codes), end='')
    
    def fatal(self, s: str, ref = None):
        if ref:
            print(ref, end = "")
        self.print(s, self.RED)
        sys.exit()

    def warn(self, s: str):
        self.print(s, self.YELLOW)

    def success(self, s: str):
        self.print(s, self.GREEN)

l = Logging()


def function_ref(path, line_no):
    sections = os.path.normpath(path).split("\\")
    name = None
    namespace = None
    folders = ""
    for [i, section] in enumerate(sections[::-1]):
        if i == 0: name = "".join(section.split(".")[:-1])
        elif section == "function":
            namespace = sections[-(i + 2)]
            break
        else: folders += section + "/"

    return l.format(f"[{namespace}:{folders}{name}:{line_no}] ", l.BOLD, l.RED)

def generic_ref(path):
    sections = os.path.normpath(path).split("\\")
    name = None
    namespace = None
    folders = ""
    for [i, section] in enumerate(sections[::-1]):
        if i == 0:
            name = section
        elif section == "data" or section == "assets":
            namespace = sections[-i]
            break
        else:
            folders += section + "/"

    return l.format(f"[{namespace}:{folders.replace(f'{namespace + '/'}', '')}{name}] ", l.BOLD, l.RED)