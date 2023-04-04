from mynt.fileutil import PackFile, PACK_FUNC, PACK_NAME
import json

executeatall = 'execute at @a as @s'

def getPlayersByOffhand(func, itemId, tag=None):
    result = f'execute at @a as @a[nbt={{Inventory:[{{id:\"{itemId}\",Slot:-106b'
    if tag:
        result = result + f',tag:{{{tag}}}}}}}]'
    else:
        result = result + '}]}]'
    return result + f' run {_getFunctionOrCmd(func)}'

def getPlayersBySelected(func, itemId, tag=None):
    result = f'execute at @a as @a[nbt={{SelectedItem:{{id:\"{itemId}\"'
    if tag:
        result = result + f',tag:{{{json.dumps(tag)}:1b}}}}'
    else:
        result = result + '}'
    return result + f'}}] run {_getFunctionOrCmd(func)}'

def exeFunction(funcName):
    return f'function {funcName}'

def ifScore(func, score, matches):
    result = ''
    if isinstance(func, (tuple, list)):
        for f in func:
            result = result + ifScore(f, score, matches) + '\n'
        return result
    else:
        return f"execute as @a if score @s {score} matches {matches} at @s run {_getFunctionOrCmd(func)}"

def ifEntityTagged(func, entityType, tag):
    return f'execute at @e[type={entityType},tag={tag}] run {_getFunctionOrCmd(func)}'

# $iftag
def ifItemByTagSelected(func, tag):
    return f'execute at @a[nbt={{SelectedItem:{{tag:{{{tag}:1b}}}}}}] positioned ~ ~1 ~ run {_getFunctionOrCmd(func)}'

def particle(type, pos='~ ~ ~', delta='0 0 0', speed=0.05, count=5):
    return f'particle {type} {pos} {delta} {speed} {count} force @a'

# $tag
def tag(type, tag, range):
    return f'tag @e[type={type},distance={range}] add {tag}'

def removeObjective(score):
    return f"scoreboard objectives remove {score}"

def addObjective(score, type="dummy"):
    return f"scoreboard objectives add {score} {type}"

def setScore(score, player='@a', amt=0):
    return f"scoreboard players set {player} {score} {amt}"

def addScore(score, player, amt=1):
    return f"scoreboard players add {player} {score} {amt}"

def timer(cache, name, timer):
    return f"execute if score {cache} {timer} matches 1.. run function {name}:timers/{timer}"

def glblIfScore(func, name, score, matches='1..'):
    result = ''
    if isinstance(func, (tuple, list)):
        for f in func:
            result = result + glblIfScore(f, name, score, matches) + '\n'
        return result
    else:
        return f"execute if score {name} {score} matches {matches} run {_getFunctionOrCmd(func)}"

def _getFunctionOrCmd(func):
    # Definitely a minecraft command
    if func[0] == '#':
        pass
    else:
        s = func.split(':')
        if len(s) > 1:
            if PackFile(PACK_FUNC + s[1] + '.mcfunction', False).exists:
                return f'function {PACK_NAME}:{s[1]}'
        else:
            return func

    return func