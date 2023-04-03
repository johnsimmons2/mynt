import mynt.logging as lg

lgl = lg.Logger.log
lgll = lg.LogLevel

def makeValidItem(item):
    if "item" not in item:
       # Simple fix, 
       lgl(lgll.WARN, f'Missing required tag \"item\".')
       return None 
    
    if "data" not in item:
        lgl(lgll.ERROR, f'No NBT Data supplied in \"data\" tag. Cannot validate item.')
        return None
    # Assume valid for now, error on user's end...
    id = item["item"]
    data = item["data"]

    # TODO: Add lore or grab textures form assets eventually with optifine.
    return item
