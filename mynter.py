import fileutil as ft
import json
import translater as tl
import entityhelp as eh
import funchelper as fh

SYNTAX_ERROR = "Cannot initialize mynt object, formatting incorrect."
TIMER_TAGS = ["name", "duration", "call"]
VAR_TAGS = ["name", "type", "data"]
VAR_TYPES = ["zombie", "item", "bool", "number", "score"]

MYNT_DEFAULTS = {
    "defaults": {
        "entity": {
            "all": {
                 "PersistenceRequired": True
            },

            "zombie": {
                "HandDropChances": [0.0, 0.0],
                "ArmorDropChances": [0.0, 0.0, 0.0, 0.0],
                "CanPickUpLoot": False
            }
        }
    }
}

class Mynt:
    def __init__(self, myntFile: ft.PackFile):
        self.myntFile = myntFile
        self.json = myntFile.get()
        self.name = ''
        self.desc = ''
        self.functions = []
        self.functions_c = []
        self.variables = []
        self.variables_c = []
        self.timers = []
        self.defaults = {}
        self.timer_c = []
        self.scores = []
        self.systemName = f"{self.name}"
        self.systemCache = f"{self.name}-c"
        self.events = {
            '$sleep': {
                'name': 'gbl_sleep',
                'event': 'minecraft.custom:minecraft.sleep_in_bed'
            }
        }
        self._initialize()
    
    def _initialize(self):
        ft.setupPack()
        self.name = self.json["packName"]
        self.desc = self.json["packDesc"]

        self.defaults = self.json["defaults"] | MYNT_DEFAULTS
        for v in self.json["variables"]:
            self.variables.append(v)
        for t in self.json["timers"]:
            self.timers.append(t)
        for f in self.json["functions"]:
            self.functions.append({f: self.json["functions"][f]})
        
        for k in self.events.keys():
            ft.load.setRaw(f"scoreboard objectives add {self.events[k]['name']} {self.events[k]['event']}")
            ft.load.setRaw(f"scoreboard players set @a {self.events[k]['name']} 0")
            eft = ft.function(f'event/{k[1:]}event')
            self.events[k]['file'] = eft
            ft.tick.setRaw(f"execute at @a as @p if score @p {self.events[k]['name']} matches 1.. run function {self.name}:event/{k[1:]}event")

        ft.load.setRaw(f"tellraw @a [{{\"text\": \"Loaded \", \"color\":\"green\"}}, {{\"text\": \"{self.desc}\", \"color\": \"red\", \"bold\": true}}]")
    
    def _closeEvent(self, event):
        self.events[event]['file'].write(f"scoreboard players set @p {self.events[event]['name']} 0")

    def _checkTags(self, tags, js):
        for t in tags:
            if not t in js:
                raise SyntaxError(SYNTAX_ERROR + f', {js}')

    def _insertDefaults(self, js: dict, typ):
        tagsToAdd = {
            "defaults": {
                "entity": {}
            }
        }
        for d in self.defaults["defaults"]:
            if d == 'entity':
                for k in self.defaults["defaults"][d].keys():
                    if k == "all" or k == typ:
                        tagsToAdd["defaults"]["entity"][typ] = self.defaults["defaults"][d][k]
                js = js | tagsToAdd["defaults"]["entity"][typ]
        return js

    def _getVarBy(self, call: str, tag='#'):
        try:
            vari = call.index('#')
            vars = call[vari+1:].split()
            var = vars[0]
            varc = None
            for v in self.variables_c:
                if v["name"] == var:
                    varc = v
                    break
            
            return varc, call[0:vari]
        except Exception as e:
            return None, None

    def _insertVariables(self, call: str):
        try:
            cmd = call.split()
            varc, commandHalf = self._getVarBy(call)
            if varc and commandHalf:
                nbt = self._insertDefaults(varc["raw"], varc["type"])
                result = commandHalf + json.dumps(nbt) + ' ' + ' '.join(cmd[2:])
                return result, varc
            else:
                return call, None
        except Exception as e:
            print(f'was no variable to insert {e}')
            return call, None
    
    def _processCall(self, call):
        if call[0] == '$':
            cmd, var = self._insertVariables(call)
            return tl.translateToMC(cmd, var)
        else:
            return self._insertVariables(call)[0]

    def _getCall(self, call):
        callStack = []
        if call:
            if isinstance(call, (list, tuple)):
                if len(call) > 1:
                    # multi-call
                    for c in call:
                        callStack.append(self._processCall(c))
            else:
                self._processCall(call)
        return callStack

    def _validateData(self, required, data):
        for k in required:
            if k not in data.keys():
                raise SyntaxError("Tried to create conditional with impropper formatting.")

    ### Functions ###
    def _initFunc(self, func):
        if 'main' in func.keys():
            for call in func['main']:
                pc = self._processCall(call)
                ft.tick.write(pc)
        elif 'load' in func.keys():
            for call in func['load']:
                pc = self._processCall(call)
                ft.load.setRaw(pc)
        else:
            f = {}
            fName = list(func.keys())[0]
            for tag in ["conditions", "body"]:
                if tag not in func[fName].keys():
                    raise SyntaxError('Missing required tag for function.')
                f[tag] = func[fName][tag]
            
            funcId = f'{len(self.functions_c)}_func'
            fc = ft.function(f'generated/{funcId}')
            cstack = []
            for b in f["body"]:
                boody = self._processCall(b)
                cstack.append(boody)
                fc.write(boody)

            # If we want to attach to an event
            for condition in f["conditions"]:
                if "event" in condition.keys():
                    ev = condition["event"]
                    if ev in self.events.keys():
                        event = self.events[ev]
                        fl = event["file"]
                        fl.write(fh.ifScore(f"{self.name}:generated/{funcId}", self.events[ev]["name"], "1.."))
                elif "if" in condition.keys():
                    ev = condition["if"]
                    if "score" in ev.keys():
                        self._validateData(["name", "matches"], ev["score"])
                        self._validateAndAddScore(ev["score"])
                        ft.tick.write(fh.ifScore(f"{self.name}:generated/{funcId}", ev["score"]["name"], ev["score"]["matches"]))

            self.functions_c.append(f)

    def _validateAndAddScore(self, score):
        if score["name"] not in self.scores:
            self.scores.append(score["name"])
            ft.load.write(fh.addObjective(score["name"]))
            ft.load.write(fh.setScore(score["name"], '@a'))
        
    ### Variables ###
    # Valid tags:
    #   name: name of variable
    #   type: entity, item, bool, number
    #   data: data related to the type
    # Data examples
    #   entity or item: nbt tag
    #   number: a number
    def _initVar(self, var):
        self._checkTags(VAR_TAGS, var)
        if not var["type"] in VAR_TYPES:
            raise TypeError(f"Type not recognized on variable {var}")
        
        if var["type"] in ["zombie", "entity"]:
            varData = eh.makeValidEntity(var["data"])
        elif var["type"] == "score":
            varData = fh.addObjective(var["name"], var["data"])
            self._validateAndAddScore(var)
            ft.load.write(varData)
        varId = len(self.variables_c)
        varc = {
            "id": varId,
            "name": var["name"],
            "type": var["type"],
            "data": json.dumps(varData),
            "raw": varData
        }
        self.variables_c.append(varc)

    ### Timers ###
    # Valid Tags:
    #   name: name of the timer
    #   duration: length of timer in seconds, * 24 for ticks
    #   call: calls a function, or calls minecraft command by default.
    def _initTimer(self, js):
        self._checkTags(TIMER_TAGS, js)
        timerId = len(self.timer_c)
        timerName = js["name"]
        systemName = f"{self.name}"
        systemCache = f"{self.name}-c"
        duration = js["duration"] * 24
        call = self._getCall(js["call"])
        # TODO: Check if call is mc command or not

        ft.load.write(fh.addObjective(timerName))
        ft.load.write(fh.setScore(timerName, systemName, 0))
        ft.load.write(fh.setScore(timerName, systemCache, 0))
        
        # Check if the timer is on in the tick function
        ft.tick.write(fh.glblIfScore(f"{systemName}:timers/{timerName}", systemCache, timerName))

        # Create timer function in the timer directory
        tf = ft.function(f"timers/{timerName}")
        tf.write(fh.addScore(timerName, systemName))
        
        for c in call:
            tf.write(fh.glblIfScore(c, systemCache, timerName, '2..'))

        tfFuncs = [fh.setScore(timerName, systemName), fh.setScore(timerName, systemCache)]
        tf.write(fh.glblIfScore(tfFuncs, systemCache, timerName, '2..'))

        # Check if the timer is done
        tf.write(fh.glblIfScore(fh.setScore(timerName, systemCache, 2), systemName, timerName, f"{duration}.."))

        self.timer_c.append(
            {
                "id": timerId,
                "name": timerName,
                "cache": systemCache,
                "duration": duration
            })
        varData = {
                    "duration": duration,
                    "name": timerName,
                    "cache": systemCache
                }
        self.variables_c.append(
            {
                "id": len(self.variables_c),
                "name": timerName,
                "type": 'timer',
                "data": json.dumps(varData),
                "raw": varData
            })

    def compile(self):
        for v in self.variables:
            self._initVar(v)

        for t in self.timers:
            self._initTimer(t)

        for i, f in enumerate(self.functions):
            self._initFunc(self.functions[i])
        
        for e in self.events:
            self._closeEvent(e)



