import json
import re


def tokenize_mfile_to_json(mfile):
    # define the format of the tokens
    tokens = {
        "KEYWORD": ["functions", "load", "main", "begin", "end", "var", "if", "then", "else", "while", "do", "score", "zombie", "entity"],
        "ID": ["[A-Za-z]+[0-9]*"],
        "NUMBER": ["[0-9]+"],
        "SYMBOL": ["+", "-", "*", "/", "=", "<", ">", "(", ")", "#", "{", "}", "\"", "..", "'", "$"],
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
                    match = re.match(re.compile("([A-Za-z]+)(?:[0-9]*)"), line)
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
            "identifiers": {
                list(set([token[1] for line in tokenized_file for token in line if token[0] == "ID"]))
            },
            "numbers": list(set([token[1] for line in tokenized_file for token in line if token[0] == "NUMBER"])),
            "symbols": list(set([token[1] for line in tokenized_file for token in line if token[0] == "SYMBOLS"]))
        }
    
    return configuration