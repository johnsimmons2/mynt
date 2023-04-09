import mynt.tokenizer
import pyparsing as pp
import mynt.logging as lg

lgl = lg.Logger.log
lgll = lg.LogLevel


def parse(tokens):
    return Parser(tokens).start()

class MyntError(SyntaxError):
    def __init__(self, *args):
        super().__init__(args)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self._ctx = "root"
        self._prevctx = "root"
        self.ast = {}
        
    def peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        else:
            return None
        
    def consume(self):
        if self.position < len(self.tokens):
            token = self.tokens[self.position]
            self.position += 1
            return token
        else:
            return None
        
    def _node(self, typ):
        return {
            "type": typ,
            "left": None,
            "right": None
        }

    def _typeCheck(self, typ, id):
        if typ != id:
            raise MyntError(f"Unexpected symbol: {self.peek()}, at {self.position}:{typ}:{id}. Context: {self._ctx}")

    # A block will end with "}" [after | before | when | $EVENT] 
    # If assignment, then it can be [from *RESOURCE*]
    def _block(self, assignment = False):
        self._prevctx = self._ctx
        self._ctx = self._ctx + f".block"
        node = self._node("BLOCK")
        blockData = ""
        token = self.consume()
        indent = 1
        if assignment:
            while token:
                if token[1] == "{":
                    indent += 1
                    blockData = blockData + token[1]
                elif token[1] == "}":
                    indent -= 1
                    blockData = blockData + token[1]
                elif token[1] != "EOL" and token[1] != "EOF":
                    blockData = blockData + token[1]
                token = self.consume()
                if indent == 0:
                    break
            if token[1] == "from":
                token = self.consume()
                resource = self._node("RESOURCE")
                resource["left"] = token[1]
                node["right"] = resource
            node["left"] = blockData
        else:
            tree = []
            while token:
                if token[1] == "{":
                    indent += 1
                elif token[1] == "}":
                    indent -= 1
                elif token[1] != "EOL" and token[1] != "EOF":
                    tree.append(self._statement())
                token = self.consume()
                if indent == 0:
                    break
            node["left"] = tree
        return node

    def _expression(self):
        node = self._node("EXPRESSION")
        tok = self.consume()
        node["left"] = tok[1]
        tok = self.consume()
        print(tok)
        if not tok[1] in ["EOL", "EOF"]:
            node["right"] = self._expression()
        return node

    def _blockOrExp(self, assignment = False):
        lgl(lgll.DEBUG, f"BLOCK_OR_EXP\t{self._ctx}")
        token = self.consume()
        nextToken = self.peek()

        result = self._node("BLOCK_OR_EXP")
        self._prevctx = self._ctx
        self._ctx = self._ctx + f".block_or_exp"


        # e.g.: `= &` | `==` | `= {`
        if token[0] == "SYMBOL":
            # Expression
            if token[1] == "{":
                result["left"] = self._block(assignment)
            else:
                result["left"] = self._expression()
            return result
        else:
            raise MyntError(f"Expected block or expression, received {token}.")

    def _isLoadableType(self, typ):
        if typ in ["zombie", "score", "item"]:
            return True
        return False

    def _getResourceFromName(self, name):
        return "dummy/resource/test.json"
    
    def _getNameFromResource(self, resource):
        return 'test-name'

    def _loadFromName(self, name):
        node = self._node("RESOURCE")
        node["left"] = name
        node["right"] = self._getResourceFromName(name)
        return node

    def _loadFromResource(self, resource):
        node = self._node("RESOURCE")
        node["left"] = self._getNameFromResource(resource)
        node["right"] = resource
        return node
    
    def _statement(self):
        #TODO: Add statement parsing.
        token = self.consume()
        print(token)
        pass

    def _assignmentStatement(self, important=False):
        isLoadableType = self._isLoadableType(self.peek()[1])
        self.consume()
        token = self.consume()
        varType = token[0]
        node = self._node("ASSIGNMENT")
        self._prevctx = self._ctx
        self._ctx = self._ctx + f".assignment.{token[1]}"

        # Make sure the type is ID
        self._typeCheck(varType, "ID")

        nextToken = self.peek()
        # Make sure the sequence is the correct grammar for this statement.
        if nextToken[1] not in ["=", "EOL", "EOF", "from"]:
            raise MyntError(f"Unexpected Symbol {self.peek()}. Expected declaration or assignment.")

        # Todo: finish
        node["left"] = token[1]
        token = self.consume()
        nextToken = self.peek()

        # End of assignment
        if token[1] in ["EOL", "EOF"]:
            if isLoadableType:
                node["right"] = self._loadFromName(node["left"])
                return node
        if isLoadableType:
            if nextToken[0] == "SYMBOL":
                if nextToken[1] == "{":
                    node["right"] = self._blockOrExp(True)
                elif nextToken[1] == "EOL" or nextToken[1] == "EOF":
                    node["right"] = self._loadFromName(token[1])
                    self.consume()
                else:
                    print('error')
                    # Error
                    pass
            elif nextToken[0] == "STRING":
                node["right"] = self._loadFromResource(nextToken[1])
                self.consume()
            else:
                node["right"] = self._expression()

        return node

    def start(self):
        self._prevctx = self._ctx
        self._ctx = self._ctx + f".prog"
        result = self._node("prog")
        result["left"] = self.parse()
        return result

    # Write a parser for the file '../grammar.txt'
    def parse(self):
        tree = []
        while self.peek():
            t = self.peek()
            if t[0] == "COMMENT" or t[0] == "WHTSPC":
                # Do not include in ast
                continue
            elif t[0] == "PRIMITIVE":

                # Must be an assignment statement
                tree.append(self._assignmentStatement())
            elif t[0] == "KEYWORD":
                if t[1] == "important":
                    self.consume()
                    tree.append(self._assignmentStatement(True))
                elif t[1] == "load":
                    tree.append(self._block())
                elif t[1] == "main":
                    tree.append(self._block())
                else:
                    raise MyntError(f"Unexpected keyword at {self.position}")

            elif t[0] == "ID":
                # Can be a function declaration in root scope.
                # Otherwise, cannot be delcaration of variable, must be statement.
                pass
            
            elif t[0] == "NUMBER":

                # 
                pass
            elif t[0] == "SYMBOL":
                if t[1] == "EOL" or t[1] == "EOF":
                    self.consume()
                    continue
            lgl(lgll.DEBUG, f"{t}, {self._ctx}")
        print(tree)
        return tree
        
