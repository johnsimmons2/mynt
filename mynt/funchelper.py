from mynt.fileutil import PackFile, PACK_FUNC, PACK_NAME

executeatall = 'execute at @a as @p'

def exeFunction(funcName):
    return f'function {funcName}'

def ifScore(func, score, matches):
    return f'execute at @a as @p if score @p {score} matches {matches} run {exeFunction(func)}'

def ifEntityTagged(func, entityType, tag):
    return f'execute at @e[type={entityType},tag={tag}] run {exeFunction(func)}'

# $iftag
def ifItemSelected(func, tag):
    return f'execute at @a[nbt={{SelectedItem:{{tag:{{{tag}:1b}}}}}}] positioned ~ ~1 ~ run {func}'

def particle(type, pos='~ ~ ~', delta='0 0 0', speed=0.05, count=5):
    return f'particle {type} {pos} {delta} {speed} {count} force @a'

# $tag
def tag(type, tag, range):
    return f'tag @e[type={type},distance={range}] add {tag}'

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