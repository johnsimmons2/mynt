import mynt as my

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
    my.lg.Logger.config_set_handler(my.lg.FormattedLogHandler())
    
    # mynt = my.Mynt(my.ft.loadMyntFile())
    # mynt.compile()

    with open('./apricot-dp.mynt') as f:
        tokens = my.tk.tokenize_mfile_to_json(f.read())
        ast = my.pa.parse(tokens)
        compiler = my.cp.Compiler(ast, f.name)
        compiler.compile()

if __name__ == "__main__":
    main()