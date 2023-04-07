import mynt.tokenizer
import pyparsing as pp


def parse(tokens):
    return Parser(tokens).start()

class MyntError(SyntaxError):
    def __init__(self, *args):
        super().__init__(args)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        
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
            "type": typ
        }

    def _typeCheck(self, typ, id):
        if typ != id:
            raise MyntError(f"Unexpected symbol: {self.peek()}, at {self.position}:{typ}:{id}")

    def _block(self):
        result = self._node("block")
        self._typeCheck(self.peek()[1], "{")
        result["block"] = self.start()["prog"]
        return result

    def _expression(self):
        pass

    def _blockOrExp(self):
        token = self.consume()
        nextToken = self.peek()

        result = self._node("block_or_expression")
        # e.g.: `= &` | `==` | `= {`
        if token[0] == "SYMBOL":
            # Expression
            if token[1] in ["EOF", "EOL"]:
                result["expression"] = self._expression()
            elif token[1] == "{":
                result["block"] = self._block()
            return result

    def _assignmentStatement(self, important=False):
        token = self.consume()
        varType = token[0]

        # Make sure the type is ID
        self._typeCheck(varType, "ID")

        # Make sure the sequence is the correct grammar for this statement.
        if self.peek()[1] not in ["=", "EOL", "EOF", "from"]:
            raise MyntError(f"Unexpected Symbol {self.peek()}. Expected declaration or assignment.")

        # Todo: finish
        if token[1]:
            pass

        result = self._node("assignment")
        result["name"] = self.peek()[1]
        result["assignment"] = self._blockOrExp()
        result["important"] = True
        return result

    def start(self):
        result = self._node("prog")
        result["prog"] = self.parse()
        return result

    # Write a parser for the file '../grammar.txt'
    def parse(self):
        while self.peek():
            t = self.consume()
            if t[0] == "COMMENT" or t[0] == "WHTSPC":
                # Do not include in ast
                continue
            elif t[0] == "PRIMITIVE":

                # Must be an assignment statement
                l = self._assignmentStatement()
                pass
            elif t[0] == "KEYWORD":
                if t[1] == "important":
                    self.consume()
                    node = self._assignmentStatement(True)
                # Expression of some kind
                pass

            elif t[0] == "ID":

                # name of function or name of variable
                pass
            
            elif t[0] == "NUMBER":

                # 
                pass
            elif t[0] == "SYMBOL":

                # Manage states
                pass
        
