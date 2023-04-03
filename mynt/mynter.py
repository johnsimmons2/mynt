import json
import mynt.fileutil as ft
import mynt.translater as tl
import mynt.entityhelp as eh
import mynt.funchelper as fh
import mynt.logging as lg
import mynt.itemhelper as ih
import sys

lgl = lg.Logger.log
lgll = lg.LogLevel

SYNTAX_ERROR = "Cannot initialize mynt object, formatting incorrect."
TIMER_TAGS = ["name", "duration", "call"]
VAR_TAGS = ["name", "type"]
VAR_TYPES = ["zombie", "item", "bool", "number", "score"]
EVENT_FILE = 'evt'

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

        # Setup Mynt Defaults.
        if not "defaults" in self.json:
            self.json["defaults"] = {}
            dftl = ft.openJSON('defaults')
            if dftl:
                self.json["defaults"] = dftl["defaults"]
                self.defaults = dftl
        self.name = self.json["packName"]
        self.desc = self.json["packDesc"]
        self.defaults = self.json["defaults"]

        # Setup the non-compiled variables.
        for v in self.json["variables"]:
            self.variables.append(v)
        for t in self.json["timers"]:
            self.timers.append(t)
        for f in self.json["functions"]:
            self.functions.append({f: self.json["functions"][f]})
        
        # Initialize the events
        for k in self.events.keys():
            # Create a scoreboard to track each event and set each players initial value to 0.
            ft.load.write(fh.addObjective(self.events[k]['name'], self.events[k]['event']))
            ft.load.write(fh.setScore(self.events[k]['name']))

            # Create the function that will be called when the event triggers.
            eft = ft.function(f'event/{k[1:]}{EVENT_FILE}')
            self.events[k]['file'] = eft

            # Setup the trigger within the tick function.
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

        for d in self.defaults:
            if d == 'entity' and typ in ['zombie', 'entity']:
                for k in self.defaults[d].keys():
                    if k == "all" or k == typ:
                        tagsToAdd["defaults"]["entity"][typ] = self.defaults[d][k]
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
            t, v, tb = sys.exc_info()
            lgl(lgll.ERROR, f'was no variable to insert {e}. [{t}, {v}, {tb}, {type(call)}]')
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
        lgl(lgll.DEBUG, f'Trying to init func... {func}')
        if 'main' in func.keys():
            for call in func['main']:
                pc = self._processCall(call)
                ft.tick.write(pc)
        elif 'load' in func.keys():
            for call in func['load']:
                pc = self._processCall(call)
                ft.load.setRaw(pc)
        else:
            funcId = f'{len(self.functions_c)}_func'
            fName = list(func.keys())[0]
            f = {
                "id": len(self.functions_c),
                "type": "function",
                "name": fName
            }
            for tag in ["conditions", "body"]:
                if tag not in func[fName].keys():
                    raise SyntaxError('Missing required tag for function.')
                f[tag] = func[fName][tag]
            
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

                    # Are we directly referencing a mynt event?
                    if ev in self.events.keys():
                        event = self.events[ev]
                        fl = event["file"]
                        fl.write(fh.ifScore(f"{self.name}:generated/{funcId}", self.events[ev]["name"], "1.."))
                    
                    # Then are we referencing an implicit event like $use?
                    else:
                        cmd = str(ev).split()
                        if len(cmd) == 1:
                            lgl(lgll.ERROR, f'Unknown implicit event: {ev}')
                        elif len(cmd) == 2:
                            c = cmd[0]
                            a = json.loads(self._insertVariables(ev)[0].split(' ', maxsplit=1)[1])

                            # Messy but works...
                            if c == "$use":
                                adv = ft.op(a["name"] + '.json', 'advancement')
                                adv.empty()
                                adv.write(json.dumps({
                                    "criteria": {
                                        fName: {
                                            "trigger": "minecraft:using_item",
                                            "conditions": {
                                                "item": {
                                                    "items": [a["item"]],
                                                    "nbt": f'{{{a["name"]}:1b}}',
                                                    "count": {
                                                        "max": 1,
                                                        "min": 1
                                                    }
                                                }
                                            },
                                        }
                                    },
                                    "rewards": {
                                        "function": f"{self.name}:generated/{funcId}"
                                    }
                                }, indent=4))
                                fc.write(f'advancement revoke @s only {self.name}:{fName}')

                            elif c == "$selected":
                                ft.tick.write(fh.ifItemSelected(fh.exeFunction(f'{self.name}:generated/{funcId}'), a["name"]))
                elif "if" in condition.keys():
                    ev = condition["if"]
                    if "score" in ev.keys():
                        # Must have name and matches tag
                        self._validateData(["name", "matches"], ev["score"])
                        # Make sure the score is loaded in the load.mcfunction if it is not referenced anywhere else.
                        self._validateAndAddScore(ev["score"]["name"])
                        ft.tick.write(fh.ifScore(f"{self.name}:generated/{funcId}", ev["score"]["name"], ev["score"]["matches"]))
            self.functions_c.append(f)

    def _validateAndAddScore(self, score):
        if score not in self.scores:
            self.scores.append(score)
            ft.load.write(fh.addObjective(score))
            ft.load.write(fh.setScore(score, '@a'))
        
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
        
        # Check if the data tag is included. If not, then check if a corresponding json exists.
        if not "data" in var:
            if var["type"] == "score":
                var["data"] = "dummy"
            else:
                js = ft.openJSON(f'{str(var["name"]).lower()}')
                if js:
                    var["data"] = js["data"]
                    if var["type"] == "item" and "item" in js:
                        var["item"] = js["item"]

                        # Optional tag that allows for creating of a scoreboard mechanic tracking use of the item.
                        if "score" in js:
                            var["score"] = js["score"]
                            # Add the objective and add to all players

                            # TODO: Need to add to when players join game if they have any objectives
                            self._validateAndAddScore(js["name"])

                            funcId = len(self.functions_c)
                            mif = ft.function(f'generated/{funcId}_func')
                            mif.empty()
                            mif.write(fh.setScore(js["name"], '@s'))
                            self.functions_c.append(self._function_c(funcId, js["name"]))

                            # Create a trigger based on the score tag
                            ft.tick.write(fh.ifScore(f"{self.name}:generated/{funcId}", js["name"], f'..{js["score"]["max"]}'))
                else:
                    lgl(lgll.ERROR, 'Variable has no matching file in the assets directory.')

        
        if var["type"] in ["zombie", "entity"]:
            varData = eh.makeValidEntity(var["data"])
        elif var["type"] == "score":
            varData = fh.addObjective(var["name"], var["data"])
            self._validateAndAddScore(var["name"])
        elif var["type"] == "item":
            varData = ih.makeValidItem(var)
        else:
            lgl(lgll.ERROR, f'Unexpected variable type received: {var["type"]}.')
            varData = None

        varId = len(self.variables_c)
        varc = self._variable_c(varId, var["name"], var["type"], json.dumps(varData), varData)

        self.variables_c.append(varc)
        lgl(lgll.DEBUG, f'Loaded variable [{var["name"]}] <{var["type"]}>')

    def _timer_c(self, timerId, timerName, duration):
        return {
                    "id": timerId,
                    "type": "timer",
                    "name": timerName,
                    "cache": self.systemCache,
                    "duration": duration
                }

    def _variable_c(self, id, name, type, data, raw):
        return {
                    "id": id,
                    "name": name,
                    "type": type,
                    "data": data,
                    "raw": raw
                }

    def _function_c(self, id, name):
        return {
                    "id": id,
                    "type": "function",
                    "name": name,
                    "body": [],
                    "conditions": []
                }
    
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

        self.timer_c.append(self._timer_c(timerId, timerName, duration))
        varData = self._timer_c(timerId, timerName, duration)
        self.variables_c.append(self._variable_c(len(self.variables_c), timerName, 'timer', json.dumps(varData), varData))
        
    def _initFile(self, js):
        if js["type"] == "score":
            pass
        elif js["type"] == "item":
            pass
        elif js["type"] == "zombie":
            pass
        else:
            lgl(lgll.WARN, js)

    def debug_printAll(self, lst, level):
        if isinstance(lst, list):
            if len(lst) > 1:
                if isinstance(lst[0], dict):
                    for v in lst:
                        lgl(level, f'\t{v["id"]}: {v["name"]}, ({v["type"]})')
                else:
                    for v in lst:
                        lgl(level, f'\t{v}')
            else:
                lgl(level, f'\t{lst}')
        else:
            lgl(level, f'\t{lst}')

    def compile(self):
        lgl(lgll.DEBUG, 'Compiling Mynt...')
        for v in self.variables:
            self._initVar(v)

        for t in self.timers:
            self._initTimer(t)

        for f in self.functions:
            self._initFunc(f)
        
        for e in self.events:
            self._closeEvent(e)
        
        # Get all files that may have been missed and try to load them as well.
        files = ft.openJSON()
        for f in files:
            if "default" not in f:
                fo = ft.openJSON(f)
                self._initFile(fo)

        lgl(lgll.DEBUG, 'Found Mynt Files: ')
        self.debug_printAll(files, lgll.DEBUG)

        lgl(lgll.SUCCESS, 'Compiled Variables')
        self.debug_printAll(self.variables_c, lgll.DEBUG)
        lgl(lgll.SUCCESS, 'Compiled Timers')
        self.debug_printAll(self.timer_c, lgll.DEBUG)
        lgl(lgll.SUCCESS, 'Compiled Functions')
        self.debug_printAll(self.functions_c, lgll.DEBUG)
        lgl(lgll.SUCCESS, 'Mynt Defaults Loaded')
        self.debug_printAll(self.defaults, lgll.DEBUG)
