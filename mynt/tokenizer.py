import re
import json


def tokenize_mfile_to_json(mfile):
    # define the format of the tokens
    tokens = {
        "KEYWORD": ["functions", "load", "main", "@a", "@s", "set", "begin", "if", "score", "zombie", "entity"],
        "ID": [r"\#([A-Za-z\-\_]+)(?:[0-9]*)"],
        "CALLOUT": [r"\$([A-Za-z\-\_]+)(?:[0-9]*)"],
        "NUMBER": ["[0-9]+"],
        "SYMBOL": ["+", "-", "*", "/", "=", "<", ">", "(", ")", "{", "}", "\"", "..", "'"],
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
                # check for keywords
                for keyword in tokens["KEYWORD"]:
                    if line.startswith(keyword):
                        line_tokens.append(("KEYWORD", keyword))
                        line = line[len(keyword):]
                        break
                
                # check for IDs
                for regex in tokens["ID"]:
                    match = re.match(re.compile(regex), line)
                    if match:
                        line_tokens.append(("ID", match.group()))
                        line = line[match.end():]
                        break
                
                for regex in tokens["CALLOUT"]:
                    match = re.match(re.compile(regex), line)
                    if match:
                        line_tokens.append(("CALLOUT", match.group()))
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
                if line.startswith(" "):
                    line = line[1:]
                # unrecognized character
                else:
                    loops = loops + 1
                    continue
                        # raise Exception("Unrecognized character: " + line[0])
            tokenized_file.append(line_tokens)
            f.write(str(line_tokens) + '\n')
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
            "ast": tokenized_file
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