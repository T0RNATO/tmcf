from tmcf.logging import l

def prompt(s: str, opt = False):
    l.print_e("> ", l.CYAN, l.BOLD)
    if opt:
        l.print_e(s + ": ", l.BOLD)
        l.print("(Optional) ", l.CYAN)
    else:
        l.print(s + ": ", l.BOLD)

def choose_option(s: str, options: list[str]):
    prompt(s, True)
    for [i, opt] in enumerate(options):
        print(f"  [{i}] " + opt)
    l.print_e("> ", l.CYAN, l.BOLD)
    l.print_e("Number: ", l.BOLD)
    return input()