import json

MYNT_COMMANDS = [
    "$summon",  # 0
    "$say",     # 1
    "$start"   # 2
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

def _condition(command: str, ctx):
    pass

def _using(command: str, ctx):
    base = MYNT_COMMAND_MAP['$using']['cmd']

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
    else:
        exc = exc + 'at @a '
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
    result = result + base + f' {json.loads(cmd[1])["cache"]} {json.loads(cmd[1])["name"]} 1'
    return result
    

def translateToMC(call: str, ctx = None):
    command = call.split()
    mc = ''
    if command[0] in MYNT_COMMAND_MAP.keys():
        cmd = command[0]
        if cmd == MYNT_COMMANDS[0]:
            mc = _summon(call, ctx)
        elif cmd == MYNT_COMMANDS[1]:
            mc = _say(call)
        elif cmd == MYNT_COMMANDS[2]:
            mc = _start(call, ctx)
        return mc
    else:
        raise SyntaxError(f'Invalid Mynt command syntax. {command}')