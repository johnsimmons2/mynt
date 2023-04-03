import os
import json
import mynt.tokenizer as tk
import mynt.logging as lg

lgl = lg.Logger.log
lgll = lg.LogLevel

PACK_NAME = 'apricot-dp'
PACK_DESC = 'Apricot: Data-Pack Demo!'
PACK_VERSION = 6
PACK_ASSETS = './assets/'
PACK_DIR = f'./dist/{PACK_NAME}/'
MC_FUNC = f'{PACK_DIR}data/minecraft/tags/functions/'
PACK_FUNC = f'{PACK_DIR}data/{PACK_NAME}/functions/'
PACK_ADVC = f'{PACK_DIR}data/{PACK_NAME}/advancements/'

MYNT_BASE_TAGS = ["functions", "variables", "timers", "packName", "packDesc"]

FILE_EXC = 'Cant get file'

class PackFile:
    def __init__(self, file, f=True):
        self.file = file
        self.exists = False
        if f:
            os.makedirs(os.path.dirname(file), exist_ok=True)
            try:
                open(self.file, 'a')
                self.exists = True
            except:
                print('failed to open')
        else:
            self.exists = os.path.exists(self.file)

    def empty(self):
        self.set('')
    
    def get(self):
        try:
            with open(self.file, 'r') as f:
                return json.loads(f.read())
        except Exception as e:
            print(FILE_EXC + f': {e}')
    
    def set(self, js):
        try:
            with open(self.file, 'w') as f:
                if js != '':
                    f.write(json.dumps(js, indent=4))
                else:
                    f.write(js)
        except Exception as e:
            print(FILE_EXC + f': {e}')
    
    def write(self, st):
        self.setRaw(st)
    
    def setRaw(self, js):
        try:
            with open(self.file, 'a+') as f:
                f.write(js)
                f.write("\n")
        except Exception as e:
            print(FILE_EXC + f': {e}')

    def append(self, js):
        try:
            with open(self.file, 'a+') as f:
                f.write(json.dumps(js, indent=4))
        except Exception as e:
            print(FILE_EXC + f': {e}')

class MyntFile(PackFile):
    def __init__(self, file):
        super().__init__(file)
        self.ast = []
    
    def _tokenizeVar(self, var):
        cmd = var.split()

        name = cmd[1][1:]
        typ = cmd[0]
        data = None

        if typ == "score":
            data = cmd[5]
        else:
            pass

        return {
            "name": name,
            "type": typ,
            "data": data
        }

    def tokenize(self, myntfile):
        pass

    def validate(self):
        myntJson = {
            "defaults": {},
            "packName": "",
            "packDesc": "",
            "variables": [],
            "timers": [],
            "functions": []
        }

        with open(self.file, 'r') as f:
            tk.first_pass(f.read())


def _checkMynt(js):
    valid = True

    # Check if the required base tags exist
    for tag in MYNT_BASE_TAGS:
        if not tag in js:
            valid = False
    return valid

def function(funcName):
    f = PackFile(PACK_FUNC + funcName + '.mcfunction')
    f.empty()
    return f

def op(funcName, ext='.mcfunction', type='function'):
    directory = ''
    match type:
        case 'function': 
            directory = PACK_FUNC
        case 'advancement': 
            directory = PACK_ADVC
            ext='.json'
        case _: print('wtf')
    return PackFile(directory + funcName + ext)

def loadMyntFile() -> PackFile:
    global PACK_NAME, PACK_DESC
    mynt = PackFile(os.path.abspath('./mynt.json'))
    
    myntf = mynt.get()
    if myntf == None:
        myntJson = {
            "defaults": {},
            "packName": 'NONE',
            "packDesc": 'NONE',
            "variables": [],
            "functions": [],
            "timers": []
        }
        mynt.set(myntJson)
    else:
        if not _checkMynt(myntf):
            raise SyntaxError("The mynt.json supplied was not formatted correctly.")
    return mynt

def openJSON(path = ''):
    if path != '':
        if not str(path).endswith('.json'):
            path = path + '.json'
        path = os.path.abspath(PACK_ASSETS + path)
        try:
            with open(path, 'r') as f:
                return json.loads(f.read())
        except:
            return None
    else:
        path = os.path.abspath(PACK_ASSETS)
        files = [f for f in os.listdir(path) 
                    if os.path.isfile(os.path.join(PACK_ASSETS, f)) and str(f).endswith('.json')]
        validFiles = []
        for f in files:
            res = {}
            with open(os.path.join(PACK_ASSETS, f), 'r') as fo:
                try:
                    res = json.loads(fo.read())
                except:
                    pass
            if "defaults" in res:
                validFiles.append(f)
            else:
                for k in ["type", "name", "data"]:
                    if k not in res:
                        lgl(lgll.ERROR, f'Could not load mynt data file [{f}]: Missing required tags.')
                else:
                    validFiles.append(f)
        return validFiles


tick: PackFile | None = None
load: PackFile | None = None

def setupPack():
    global tick, load
    mcmeta = PackFile(PACK_DIR + 'pack.mcmeta')
    mtick = PackFile(MC_FUNC + 'tick.json')
    mload = PackFile(MC_FUNC + 'load.json')

    mcmeta_f = {
            "pack": {
                "pack_format": PACK_VERSION,
                "description": PACK_DESC
            }
        }
    mtick_f = {
        "values": [f'{PACK_NAME}:tick']
    }
    mload_f = {
        "values": [f'{PACK_NAME}:load']
    }

    mcmeta.set(mcmeta_f)
    mtick.set(mtick_f)
    mload.set(mload_f)

    tick = PackFile(PACK_FUNC + 'tick.mcfunction')
    load = PackFile(PACK_FUNC + 'load.mcfunction')
    tick.empty()
    load.empty()

    os.makedirs(PACK_ADVC, exist_ok=True)

