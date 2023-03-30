import fileutil as ft
from mynter import Mynt

# TODO:
#   - Global timer progress bars
#   - Item casting progress bar
#   - More condition types
#       - All entities with a given tag are dead
#       - Any score matches
#   - Create and reference marker armor stands
#   - Functions call other functions in their body
#   - Functions wait or schedule for other things
#   - Abide by standard practice data packs
#   - Use optifine so that I can automatically generate resource pack
#   - Separate assets folder for custom images or items
#       - Custom items like a summoning spell with bossbar all described in one file, with recipes
#   - Keep track of what variables to reset to 0 or not when reloading


def main():
    mynt = Mynt(ft.loadMyntFile())
    m = ft.MyntFile('./apricot.mynt')
    m.validate()
    mynt.compile()


if __name__ == "__main__":
    main()