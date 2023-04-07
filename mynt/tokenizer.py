import re
import json

# CALLABLE -> FUNC | EVENT
# FUNC -> 
#   { EXPRESSION+ } 
# | { EXPRESSION+ } after CALLABLE DURATION
# | { EXPRESSION+ } when CALLABLE
# | { EXPRESSION+ } 
# EXPRESSION -> 
#   if CONDITION STATEMENT
# | if CONDITION STATEMENT else STATEMENT
# | STATEMENT
# { STATEMENT* }
# \s
# STATEMENT ->
#   TYPE id = EXPRESSION
# | run FUNC
# | MYNTCMD
# | TERM
# TERM -> value of variable


def tokenize_mfile_to_json(mfile):
    # define the format of the tokens
    tokens = {
        "COMMENT": [
            r"\/[\/]+.*"
        ],
        "KEYWORD": [
            "load", 
            "main", 
            "run", 
            "delay", 
            "if",
            "else",
            "after",
            "when",
            "important",
            "from"
            ],
        "PRIMITIVE": [
            "score",
            "number",
            "zombie"
        ],
        "STRING": [r"\"([A-Za-z\-\_\/\\]+)([0-9]*)\"", r"'([A-Za-z\-\_]+)([0-9]*)'"],
        "ID": [r"([a-z\-\_]+)([0-9]*)"],
        "NUMBER": ["[0-9]"],
        "SYMBOL": ["+", "-", "*", "/", "=", "<", ">", "(", ")", "{", "}", "\"", ".", "'", ","],
        # add more tokens as needed
    }
    # tokenize the mfile
    tokenized_file = []
    lines = mfile.split("\n")
    with open('./results1.json', 'w+') as f:
        for line in lines:
            loops = 0   
            line_tokens = []
            while line and loops < 10:
                mtch = re.match(re.compile(tokens["COMMENT"][0]), line)
                if mtch:
                    line = line[mtch.end():]
                    break

                # check for keywords
                for keyword in tokens["KEYWORD"]:
                    if line.startswith(keyword):
                        line_tokens.append(("KEYWORD", keyword))
                        line = line[len(keyword):]
                        break

                for keyword in tokens["PRIMITIVE"]:
                    if line.startswith(keyword):
                        line_tokens.append(("PRIMITIVE", keyword))
                        line = line[len(keyword):]
                        break

                for regex in tokens["STRING"]:
                    match = re.match(re.compile(regex), line)
                    if match:
                        print(match)
                        line_tokens.append(("STRING", match.group()))
                        line = line[match.end():]
                        break
                
                # check for IDs
                for regex in tokens["ID"]:
                    match = re.match(re.compile(regex), line)
                    if match:
                        line_tokens.append(("ID", match.group()))
                        line = line[match.end():]
                        break

                # check for numbers
                for regex in tokens["NUMBER"]:
                    match = re.match(re.compile(regex), line)
                    if match:
                        line_tokens.append(("NUMBER", match.group()))
                        line = line[match.end():]
                        break

                # check for symbols
                for symbol in tokens["SYMBOL"]:
                    if line.startswith(symbol):
                        line_tokens.append(("SYMBOL", symbol))
                        line = line[len(symbol):]
                        break

                # ignore whitespace
                if line.startswith("\n"):
                    line = line[1:]
                    line_tokens.append(("SYMBOL", "NWLN"))
                elif line.startswith(" "):
                    line = line[1:]
                elif line.startswith(""):
                    line_tokens.append(("SYMBOL", "EOL"))
                    line = line[1:]
                # unrecognized character
                else:
                    loops = loops + 1
                    continue
                        # raise Exception("Unrecognized character: " + line[0])
            if len(line_tokens) > 0:
                tokenized_file.append(line_tokens)
            f.write(str(line_tokens) + '\n')
        tokenized_file.append([("SYMBOL", "EOF")])
        # convert the tokenized file to a JSON configuration
        configuration = {
            "keywords": list(set([token[1] for line in tokenized_file for token in line if token[0] == "KEYWORD"])),
            "callouts": [{
                f"{token[1]}": {
                    "flag": tokenized_file[i][j-1][1],
                    "type": token[0]
                }
            } for i, l in enumerate(tokenized_file) for j, token in enumerate(l) if token[0] == "CALLOUT"],
            "identifiers": list(set([
                token[1] for i, l in enumerate(tokenized_file) for j, token in enumerate(l) if token[0] == "ID"])),
            "numbers": list(set([token[1] for line in tokenized_file for token in line if token[0] == "NUMBER"])),
            "symbols": list(set([token[1] for line in tokenized_file for token in line if token[0] == "SYMBOLS"])),
            "ast": [item for sublist in tokenized_file for item in sublist]
        }
    
    return configuration

def first_pass(file):
    with open('./results.json', 'w+') as f:
        result = tokenize_mfile_to_json(file)
            
        valid = True
        f.write(json.dumps(result, indent=4))
        required = ["functions", "main", "load"]
        for k in required:
            if k not in result["keywords"]:
                valid = False

        if valid:
            mnt = {
                "packName": "",
                "packDesc": "",
                "functions": {},
                "defaults": {},
                "variables": [],
                "timers": [],
            }

            state = 0
            funcName = ''
            for i, t in enumerate(result["ast"]):
                if t:
                    for j, q in enumerate(t):
                        if q[1] == "{":
                            state = state + 1
                            funcName = t[0][1]
                            mnt["functions"][f"{funcName}"] = {
                                "body": [],
                                "conditions": []
                            }
                            continue
                        elif q[1] == "}":
                            state = state - 1
                        elif state > 0:
                            if q[1] == "$":
                                cmd = q[1] + ' '.join(list(map((lambda x : x[1]), t[1:])))
                                if not mnt["functions"][f"{funcName}"]["body"]:
                                    mnt["functions"][f"{funcName}"]["body"] = []
                                mnt["functions"][f"{funcName}"]["body"] = mnt["functions"][f"{funcName}"]["body"].append(cmd)
            if state != 0:
                pass
                #raise ValueError("Mismatching braces {}")
            
            with open('./mynt-demo.json', 'w+') as my:
                my.write(json.dumps(mnt, indent=4))