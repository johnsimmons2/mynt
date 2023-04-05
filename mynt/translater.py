import json
import mynt.funchelper as fh
import mynt.fileutil as ft

MYNT_COMMANDS = [
    "$summon",      # 0
    "$say",         # 1
    "$start",       # 2
    "$tag",         # 3
    "$iftag",       # 4
    "$particle",    # 5
    "$if",          # 6
    "$then",        # 7
    "$mark",         # 8
]

MYNT_COMMAND_MAP = {
    MYNT_COMMANDS[0]: {
        "cmd": "summon",
        "params": [
            "as",
            "at",
            "coords"
        ]
    },
    MYNT_COMMANDS[1]: {
        "cmd": "tellraw",
        "params": [
            "to",
            "color",
            "bold",
            "underline",
            "italic"
        ]
    },
    MYNT_COMMANDS[2]: {
        "cmd": "scoreboard players set"
    },
    MYNT_COMMANDS[3]: {
        "cmd": "tag @e"
    },
    MYNT_COMMANDS[4]: {
        "cmd": "execute at @e"
    },
    MYNT_COMMANDS[5]: {
        "cmd": "particle"
    },
    MYNT_COMMANDS[6]: {
        "cmd": "execute as @a if"
    },
    MYNT_COMMANDS[7]: {
        "cmd": ""
    },
    MYNT_COMMANDS[8]: {
        "cmd": "summon minecraft:armor_stand ~ ~ ~ {ShowArms:1b,Invisible:1b,Marker:1b,Tags:["
    }
}

MYNT_SAY_PARAMS = {
    "$red": {
        "color": "red"
    },
    "$blue": {
        "color": "blue"
    },
    "$green": {
        "color": "green"
    },
    "$bold": {
        "bold": True
    },
    "$italic": {
        "italic": True
    },
    "$underline": {
        "underline": True
    }
}

#   mynt.json is formatted into functions with code bodies and conditions
#   that is passed to the translater along with all mynt code


def _handleFunction(func, ctx):
    pass

def _handleCondition(command: str, ctx):
    pass

def _using(command: str, ctx):
    base = MYNT_COMMAND_MAP['$using']['cmd']

def _then(command: str, ctx):
    cmd = command.split(maxsplit=1)
    callout = translateToMC(cmd[1])
    fil = ft.op(ctx["metadata"], type='condition')
    fil.write(callout)
    return None

# $if <score|selected|offhand|hastag|nasnbt|near> [#]<var>
# Stores the result in a scoreboard. 
def _if(command: str, ctx):
    base = MYNT_COMMAND_MAP['$if']['cmd']
    cmd = command.split(maxsplit=3)
    req = cmd[1]
    result = ''
    if "score" in req:
            # if score was supplied in the context it should have a max value to set the condition from.
        if "score" in ctx:
            if "max" in ctx:
                result = f'{base} {req} @p {cmd[2]} matches {ctx["score"]["max"]}..'    
        
            # Create the callout for the predicate
        callout = ft.op(ctx["metadata"], type='condition')
        callout.empty()
        print(callout.functionName())
        result = f'{base} {req} @s {cmd[2]} {cmd[3]} at @s as @s run function {callout.functionName()}'
    else:
        raise SyntaxError("Unknown predicate in if statement")
    return result + ''

def _mark(command: str, ctx):
    cmd = command.split()
    if len(cmd) == 3:
        print(cmd[2])
    base = MYNT_COMMAND_MAP['$mark']['cmd']
    result = base + f'{cmd[1]}]}}'
    return result

def _summon(command: str, ctx):
    base = MYNT_COMMAND_MAP['$summon']['cmd']
    cmd = command.split()
    typ = ''
    data = ''
    if ctx:
        typ = ctx["type"]
        data = ' '+ ctx["data"]
    else:
        typ = cmd[1]
    result = typ + ' ~ ~ ~' + data
    prefix = ''
    for i, c in enumerate(cmd):
        # Skip '$summon'
        if i == 0:
            continue
        
        # Add the as and at parameters
        if c == 'as' or c == 'at':
            prefix = prefix + c + ' ' + cmd[i+1] + ' '
    
    exc = 'execute '
    if prefix != '':
        exc = exc + prefix
    exc = exc + 'run ' + base + ' ' + result
    return exc

def _say(command: str):
    tagsToAdd = {}
    base = MYNT_COMMAND_MAP['$say']['cmd']
    cmd = command.split()
    txt = ''
    for c in cmd:
        if c in MYNT_SAY_PARAMS.keys():
            key = next(iter(MYNT_SAY_PARAMS[c]))
            val = MYNT_SAY_PARAMS[c][key]
            tagsToAdd[key] = val
        elif c[0] == '@':
            if len(c) > 2:
                base = base + ' ' + c[1:]
            else:
                base = base + ' @a'
        elif c[0] != '$':
            txt = txt + ' ' + c
    result = base + ' ' + json.dumps({
        "text": txt
    } | tagsToAdd)
    return result

def _start(command: str, ctx):
    base = MYNT_COMMAND_MAP['$start']['cmd']
    result = ''
    cmd = command.split(maxsplit=1)
    if len(cmd) != 2:
        raise SyntaxError('Start command has only one parameter')
    result = result + base + f' @s {cmd[1].lower().strip("#")}_c 1'
    return result
    
def _tag(call, ctx):
    base = MYNT_COMMAND_MAP['$tag']['cmd']
    cmd = call.split()
    result = base + f'[type={cmd[1]},distance={cmd[3]}] add {cmd[2]}'
    return result

def _particle(call, ctx):
    base = MYNT_COMMAND_MAP['$particle']['cmd']
    cmd = call.split()
    result = base + f' {cmd[1]} ~ ~ ~ 0 0 0 0.05 5 force @a'
    return result

# $iftag [type]{nbt} [callout]
def _iftag(call, ctx):
    base = MYNT_COMMAND_MAP['$iftag']['cmd']
    cmd = str(call).split(maxsplit=2)
    nbt = ''
    if '.' in cmd[1]:
        nbt = cmd[1].split('.')[1]
        cmd[1] = cmd[1].split('.')[0]
    result = base + f'[tag={cmd[1]}'
    if nbt != '':
        result = result + f',nbt={nbt}'
    result = result + f'] run '
    callout = translateToMC(cmd[2])
    return result + callout

def translateToMC(call: str, ctx = None):
    command = call.split()
    mc = ''
    if command[0][0] == '$':
        if command[0] in MYNT_COMMAND_MAP.keys():
            cmd = command[0]
            if cmd == MYNT_COMMANDS[0]:
                mc = _summon(call, ctx)
            elif cmd == MYNT_COMMANDS[1]:
                mc = _say(call)
            elif cmd == MYNT_COMMANDS[2]:
                mc = _start(call, ctx)
            elif cmd == MYNT_COMMANDS[3]:
                mc = _tag(call, ctx)
            elif cmd == MYNT_COMMANDS[4]:
                mc = _iftag(call, ctx)
            elif cmd == MYNT_COMMANDS[5]:
                mc = _particle(call, ctx)
            elif cmd == MYNT_COMMANDS[6]:
                mc = _if(call, ctx)
            elif cmd == MYNT_COMMANDS[7]:
                mc = _then(call, ctx)
            elif cmd == MYNT_COMMANDS[8]:
                mc = _mark(call, ctx)
            return mc
        else:
            raise SyntaxError(f'Invalid Mynt command syntax. {command}')
    else:
        return call