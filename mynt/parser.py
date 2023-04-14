import json
import mynt.tokenizer
import pyparsing as pp
import mynt.logging as lg
from enum import Enum

lgl = lg.Logger.log
lgll = lg.LogLevel

KEYWORDS = [
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
            ]


class ASTNodeType(Enum):
    PROGRAM = 0,
    STATEMENT = 1,
    ASSIGNMENT_STATEMENT = 2,
    FUNCTION = 3,
    RESOURCE = 4,
    BLOCK = 5,
    JSON = 6,
    EXPRESSION = 7,
    NUMBER = 8,
    IDENTIFIER = 9,
    RUN_STATEMENT = 10,
    IF_STATEMENT = 11,
    MC_STATEMENT = 12,
    LOADABLE_TYPE = 13,
    STRING = 14
class ASTNode:
    def __init__(self, typ: ASTNodeType, parent = None):
        self.type = typ
        self.parent = parent

    def __repr__(self):
        return f"{self.type}"

    # Print the current node with all of its children formatted in a nested tree
    # Explicitly for debugging
    def printNode(self, indent = 0):
        result = " " * indent + str(self.type) + ": "
        if isinstance(self, IdentifierNode):
            result = result + f"(\'{self.name}\')"
        elif isinstance(self, NumberNode):
            result = result + f"({self.value})"
        elif isinstance(self, FunctionNode):
            result = result + f"(\'{self.name}\', {self.body})"
        elif isinstance(self, StatementNode):
            result = result + f"({self.__class__.__name__}"
            if isinstance(self, RunStatementNode):
                result = result + f", {self.function.name}, {self.delay}"
            result = result + ")"
        elif isinstance(self, ExpressionNode):
            result = result + f"({self.left}, {self.operator}, {self.right})"
            result = result + ")"
        print(result)
        for child in self.__dict__:
            if child == "parent":
                continue
            if isinstance(self.__dict__[child], ASTNode):
                self.__dict__[child].printNode(indent + 2)
            elif isinstance(self.__dict__[child], list):
                for item in self.__dict__[child]:
                    if isinstance(item, ASTNode):
                        item.printNode(indent + 2)
                    else:
                        print(" " * (indent + 2) + str(item))

class IdentifierNode(ASTNode):
    def __init__(self, id, parent = None):
        super().__init__(ASTNodeType.IDENTIFIER, parent)
        self.name = id

class NumberNode(ASTNode):
    def __init__(self, value, parent = None):
        super().__init__(ASTNodeType.NUMBER, parent)
        self.value = value

class StringNode(ASTNode):
    def __init__(self, value, parent = None):
        super().__init__(ASTNodeType.STRING, parent)
        self.value = value

class LoadableTypeNode(ASTNode):
    def __init__(self, name, parent = None):
        super().__init__(ASTNodeType.LOADABLE_TYPE, parent)
        self.name = name

class DurationNode(NumberNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.unit = None
class StatementNode(ASTNode):
    def __init__(self, parent = None):
        super().__init__(ASTNodeType.STATEMENT, parent)

class MCStatementNode(StatementNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.mcCommand = None

class IfStatementNode(StatementNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.condition = None
        self.then = None
        self.otherwise = None

class RunStatementNode(StatementNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.function = None
        self.delay = None

class ResourceNode(ASTNode):
    def __init__(self, parent = None):
        super().__init__(ASTNodeType.RESOURCE, parent)
        self.name = None
        self.resource = None

class BlockNode(ASTNode):
    def __init__(self, parent = None):
        super().__init__(ASTNodeType.BLOCK, parent)
        self.name = None
        self.data = None
        self.neighborBlock = None
class JSONNode(BlockNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.json = None
class ExpressionNode(ASTNode):
    def __init__(self, parent = None):
        super().__init__(ASTNodeType.EXPRESSION, parent)
        self.left = None
        self.right = None
        self.operator = None

class ProgramNode(ASTNode):
    def __init__(self, parent = None):
        super().__init__(ASTNodeType.PROGRAM, parent)
        self.statements = []

class FunctionNode(BlockNode):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.body = None
        self.after = None
        self.when = None
        self.before = None
        self.event = None

class AssignmentNode(ASTNode):
    def __init__(self, parent = None):
        super().__init__(ASTNodeType.ASSIGNMENT_STATEMENT, parent)
        self.variable = None
        self.assignment = None
        self.important = False

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
        if isinstance(typ, ASTNodeType):
            match typ:
                case ASTNodeType.ASSIGNMENT_STATEMENT:
                    return AssignmentNode()
                case ASTNodeType.FUNCTION:
                    return FunctionNode()
                case ASTNodeType.PROGRAM:
                    return ProgramNode()
                case ASTNodeType.RESOURCE:
                    return ResourceNode()
                case ASTNodeType.BLOCK:
                    return BlockNode()
                case ASTNodeType.JSON:
                    return JSONNode()
                case ASTNodeType.EXPRESSION:
                    return ExpressionNode()    
                case ASTNodeType.NUMBER:
                    return NumberNode()
                case ASTNodeType.IDENTIFIER:
                    return IdentifierNode()
                case ASTNodeType.RUN_STATEMENT:
                    return RunStatementNode()
                case ASTNodeType.IF_STATEMENT:
                    return IfStatementNode()
                case ASTNodeType.MC_STATEMENT:
                    return MCStatementNode()
                case ASTNodeType.STRING:
                    return StringNode()
                case ASTNodeType.LOADABLE_TYPE:
                    return LoadableTypeNode()

    def _condition(self):
        condition = self._expression()
        return condition

    def _jsonStatement(self):
        jsonNode = self._node(ASTNodeType.JSON)
        js = {}
        indent = 1
        while self.consume()[1] != "}" and indent != 0:
            if self.peek()[0] == "STRING":
                key = str(self.consume()[1]).strip("\"")
                colon = self.consume()
                valtok = self.consume()
                if valtok[1] == "{":
                    indent += 1
                    val = self._jsonStatement().data
                else:
                    if valtok[0] == "STRING":
                        val = str(valtok[1]).strip("\"")
                    elif valtok[0] == "NUMBER":
                        val = float(valtok[1])
                js[key] = val
            elif self.peek()[1] == "{":
                indent += 1
            elif self.peek()[1] == "}":
                indent -= 1
        jsonNode.data = js
        try:
            jso = json.dumps(js)
            jsonNode.json = jso
        except Exception as e:
            raise MyntError(f"Invalid JSON: {e} at {self.position}")
        return jsonNode

    def _statement(self):
        lgl(lgll.DEBUG, f"STATEMENT: {self.position}")
        token = self.consume()
        if token[0] == "SYMBOL" and token[1] == "{":
            raise MyntError("Unexpected symbol '{'")
        elif token[0] == "ID":
            # If the current statement is an ID followed by an equals, it is an assignment.
            if self.peek()[1] == "=":
                node = self._blockOrExp(True)
                asNode = self._node(ASTNodeType.ASSIGNMENT_STATEMENT)
                asNode.variable = IdentifierNode()
                asNode.variable.name = token[1]
                asNode.assignment = node
                return asNode
            # Otherwise, since it was not caught as a keyword, it must be line of mcfunction code.
            # If this is the case, it is likely to include json data since you cannot declare a function
            # within another function.
            else:
                node = self._node(ASTNodeType.MC_STATEMENT)
                # Get the entire line of code, if it contains a curly brace, it is a json object.
                command = f"{token[1]}"
                nt = self.consume()
                while nt[1] != "EOL":
                    if nt[1] == "{":
                        jsn = self._jsonStatement()
                        command += f" {jsn.json}"
                    else:
                        command += f" {nt[1]}"
                    nt = self.consume()
                node.mcCommand = command
                return node

        elif token[0] == "KEYWORD":
            if token[1] == "run":
                lgl(lgll.DEBUG, f"RUN STATEMENT: {self.position}")
                run = RunStatementNode()
                
                # Get the name of the function which should be the next token
                funcName = self.consume()[1]
                func = IdentifierNode()
                func.parent = run
                func.name = funcName
                run.function = func

                if self.peek()[0] == "KEYWORD":
                    token = self.consume()
                    if token[1] == "delay":
                        if self.peek()[0] != "NUMBER":
                            raise MyntError(f"Unexpected token: {self.peek()[1]}")
                        run.delay = self.peek()[1]
                elif self.peek()[1] != "EOL":
                    raise MyntError(f"Unexpected run statement syntax at: {self.peek()[1]}")

                return run
            elif token[1] == "if":
                try:
                    lgl(lgll.DEBUG, f"IF STATEMENT: {self.position}")
                    statement = self._node(ASTNodeType.IF_STATEMENT)
                    expr = self._expression()
                    statement.condition = expr
                    statement.then = self._block()
                    if self.peek()[1] == "else":
                        self.consume()
                        statement.otherwise = self._block()
                    return statement
                except Exception as e:
                    raise MyntError(f"Unexpected if statement syntax; expected block, got: {e}")
            else:
                raise MyntError(f"Unexpected keyword: {token}")
        else:
            raise MyntError(f"Unexpected token: {token}")


    def _typeCheck(self, typ, id):
        if typ != id:
            raise MyntError(f"Unexpected symbol: {self.peek()}, at {self.position}:{typ}:{id}. Context: {self._ctx}")

    # Parse a block of code given the first token is "{", create a node representing the block
    # A block may have a neighbor block, e.g. `block from resource`
    def _block(self, assignment = False):
        lgl(lgll.DEBUG, f"BLOCK: {self.position}")
        self._prevctx = self._ctx
        self._ctx = self._ctx + f".block"
        blockData = ""
        token = self.consume()
        indent = 0

        # Must be JSON
        if assignment:
            node = self._node(ASTNodeType.BLOCK)
            node.name = token[1]
            while token:
                if token[1] == "{":
                    indent += 1
                    blockData = blockData + token[1]
                elif token[1] == "}":
                    indent -= 1
                    blockData = blockData + token[1]
                elif token[1] != "EOL" and token[1] != "EOF":
                    blockData = blockData + token[1]
                if indent == 0:
                    break
                token = self.consume()
            if token[1] == "from":
                token = self.consume()
                resource = self._node(ASTNodeType.RESOURCE)
                resource.name = token[1]
                node.neighborBlock = resource
            node.data = blockData
            return node
        else:
            node = self._node(ASTNodeType.FUNCTION)
            if token[1] == "{":
                node.name = "anonymous"
            else:
                node.name = token[1]
                token = self.consume()
            tree = []
            while token:
                if token[1] == "{":
                    indent += 1
                    token = self.consume()
                elif token[1] == "}":
                    indent -= 1
                    token = self.consume()
                elif token[1] == "EOL" or token[1] == "EOF":
                    self.consume()
                else:
                    statement = self._statement()
                    statement.parent = node
                    tree.append(statement)
                if indent == 0:
                    break
                token = self.peek()
            node.body = tree
            return node
        
    def _atom(self, token):
        if token[0] == "NUMBER":
            return NumberNode(float(token[1]))
        elif token[0] == "STRING":
            return StringNode(token[1])
        elif token[0] == "ID":
            return IdentifierNode(token[1])
        else:
            raise MyntError(f"Unexpected atom: {token}")

    def _expression(self):
        node = self._node(ASTNodeType.EXPRESSION)
        tok = self.consume()
        node.left = self._atom(tok)
        if self.peek()[1] in ["+", "*", "-", "/", "**", "<", ">", "<=", ">=", "==", "and", "or"]:
            tok = self.consume()
            node.operator = tok[1]
            node.right = self._expression()
        elif self.peek()[1] == "{":
            return node
        else:
            if self.peek()[1] != "EOL":
                raise MyntError(f"Unknown expression syntax: {tok}, {node.left}, {self.peek()}")
        return node

    def _blockOrExp(self, assignment = False):
        lgl(lgll.DEBUG, f"BLOCK_OR_EXP\t{self._ctx}")
        token = self.consume()

        node = None
        self._prevctx = self._ctx
        self._ctx = self._ctx + f".block_or_exp"

        # e.g.: `= &` | `==` | `= {`
        if token[0] == "SYMBOL":
            # Expression
            if token[1] == "{":
                node = self._block(assignment)
            else:
                node = self._expression()
            return node
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
        node = self._node(ASTNodeType.RESOURCE)
        node["left"] = name
        node["right"] = self._getResourceFromName(name)
        return node

    def _loadFromResource(self, resource):
        node = self._node("RESOURCE")
        node["left"] = self._getNameFromResource(resource)
        node["right"] = resource
        return node
    
    def _assignmentStatement(self, important=False):
        isLoadableType = self._isLoadableType(self.peek()[1])
        self.consume()
        token = self.consume()
        varType = token[0]

        node = self._node(ASTNodeType.ASSIGNMENT_STATEMENT)
        self._prevctx = self._ctx
        self._ctx = self._ctx + f".assignment.{token[1]}"

        # Make sure the type is ID
        self._typeCheck(varType, "ID")

        nextToken = self.peek()
        # Make sure the sequence is the correct grammar for this statement.
        if nextToken[1] not in ["=", "EOL", "EOF", "from"]:
            raise MyntError(f"Unexpected Symbol {self.peek()}. Expected declaration or assignment.")

        # Todo: finish
        node.variable = token[1]
        token = self.consume()
        nextToken = self.peek()

        # End of assignment

        # If there is a loadable type, then there may be an equals sign, a from keyword, or nothing.
        if isLoadableType:
            lgl(lgll.DEBUG, f"LOADABLE_TYPE\t{self._ctx}")
            # If there was no equal sign nor a from keyword, then we will try to load the variable by its name and context.
            if token[1] in ["EOL", "EOF"]:
                node.assignment = self._loadFromName(node.variable)
                return node
            if token[1] == "=":
                if nextToken[0] == "SYMBOL":
                    if nextToken[1] == "{":
                        assignment = self._block(assignment=True)
                        assignment.parent = node
                        node.assignment = assignment
                    elif nextToken[1] == "EOL" or nextToken[1] == "EOF":
                        resource = self._loadFromName(token[1])
                        resource.parent = node
                        node.assignment = resource
                    else:
                        raise MyntError(f"Unexpected symbol {nextToken[1]} after equal sign.")
                elif nextToken[0] == "STRING":
                    node["right"] = self._loadFromResource(nextToken[1])
                    self.consume()
                else:
                    node["right"] = self._expression()
            else:
                raise MyntError(f"Unexpected end of statement with unknown symbol {token[1]}")
        else:
            lgl(lgll.DEBUG, f"NOT_LOADABLE_TYPE\t{self._ctx}")
            if token[1] == "=":
                if nextToken[1] != "EOL" and nextToken[1] != "EOF":
                        node.assignment = self._expression()
                else:
                    raise MyntError(f"Unexpected symbol {nextToken[1]} after equal sign.")
            else:
                raise MyntError(f"Unexpected end of statement with unknown symbol {token[1]}")
        return node

    def start(self):
        return self.parse()

    # Write a parser for the file '../grammar.txt'
    def parse(self):
        foundLoad = False
        foundMain = False
        tree = []
        contextNode = self._node(ASTNodeType.PROGRAM)
        currentContext = contextNode
        while self.peek():
            t = self.peek()
            self._ctx = self._prevctx
            if t[0] == "COMMENT" or t[0] == "WHTSPC":
                # Do not include in ast
                continue
            elif t[0] == "PRIMITIVE":
                # Must be an assignment statement
                node = self._assignmentStatement()
                node.parent = currentContext
                tree.append(node)
            elif t[0] == "KEYWORD":
                if t[1] == "important":
                    self.consume()
                    node = self._assignmentStatement(True)
                    node.parent = currentContext
                    tree.append(node)
                elif t[1] == "load":
                    if foundLoad:
                        raise MyntError(f"Found multiple load statements.")
                    foundLoad = True
                    loadNode = self._block()
                    loadNode.parent = currentContext
                    tree.append(loadNode)
                elif t[1] == "main":
                    if foundMain:
                        raise MyntError(f"Found multiple main statements.")
                    foundMain = True
                    mainNode = self._block()
                    mainNode.parent = currentContext
                    tree.append(mainNode)
                else:
                    raise MyntError(f"Unexpected keyword at {self.position}, {t}")

            elif t[0] == "ID":
                # Can be a function declaration in root scope.
                blockNode = self._block()
                blockNode.parent = currentContext
                tree.append(blockNode)
                # Otherwise, cannot be delcaration of variable, must be statement.
            
            # used?
            elif t[0] == "NUMBER":

                # 
                pass
            elif t[0] == "SYMBOL":
                if t[1] == "EOL" or t[1] == "EOF":
                    self.consume()
                    continue
        contextNode.statements = tree
        return contextNode
        
