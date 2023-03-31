def validateHands(hands):
    def _innerObjValidate(obj):
        if "Count" not in obj.keys():
            obj["Count"] = 1
        return obj
    lhand = {}
    rhand = {}
    items = hands["HandItems"]
    for i, m in enumerate(items):
        print(m)
        if i == 0:
            lhand = _innerObjValidate(m)
        elif i == 1:
            rhand = _innerObjValidate(m)
    hands["HandItems"] = [
        lhand, rhand
    ]
    return hands

def validateArmor(armor):
    def _innerObjValidate(obj):
        if "Count" not in obj.keys():
            obj["Count"] = 1
        return obj
    helmet = {}
    chest = {}
    pants = {}
    boots = {}
    items = armor["ArmorItems"]
    for i, m in enumerate(items):
        if "chestplate" in m["id"]:
            chest = _innerObjValidate(m)
        elif "leggings" in m["id"]:
            pants = _innerObjValidate(m)
        elif "boots" in m["id"]:
            boots = _innerObjValidate(m)
        elif "helmet" in m["id"]:
            helmet = _innerObjValidate(m)
    armor["ArmorItems"] = [
        boots, pants, chest, helmet
    ]
    return armor
        
def makeValidEntity(js):
    nbt = js
    if "HandItems" in js.keys():
        nbt = validateHands(nbt)
    if "ArmorItems" in js.keys():
        nbt = validateArmor(nbt)
    return nbt
