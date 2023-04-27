from mynt.parser import ASTNode, ASTNodeType, AssignmentNode, BlockNode, ExpressionNode, IdentifierNode, MCStatementNode, MyntError, NumberNode, ProgramNode, FunctionNode, RunStatementNode, IfStatementNode
from mynt.logging import Logger, LogLevel
import mynt.funchelper as fh
import json

lgl = Logger.log
lgll = LogLevel

class MyntCompilerError(MyntError):
    def __init__(self, message):
        super().__init__(message)

class Compiler:
    def __init__(self, ast, filename):
        self.ast = ast
        self.main = None
        self.load = None
        self.filename = filename
        self.myntjson = {}

    def validateIdentifier(self, identifier: str):
        pass

    def op(self, left, right, op):
        match op:
            case "+":
                return left + right
            case "-":
                return left - right
            case "*":
                return left * right
            case "/":
                return left / right
            case "%":
                return left % right
            case ">":
                return left > right
            case "<":
                return left < right
            case ">=":
                return left >= right
            case "<=":
                return left <= right
            case "==":
                return left == right
            case "!=":
                return left != right
            case _: 
                return None
            
    def evaluate(self, expression: ExpressionNode):
        if isinstance(expression, IdentifierNode):
            if not self.validVariable(expression.name):
                raise MyntCompilerError(f"Variable {expression.name} is not defined.")
            else:
                var = list(filter(lambda x: x["name"] == expression.name, self.myntjson["variables"]))[0]
                return var["data"]
        elif isinstance(expression, ExpressionNode):
            # Evaluate the left-hand side
            left = self.evaluate(expression.left)

            # Evaluate the right-hand side
            right = self.evaluate(expression.right)

            # Combine the left and right-hand sides using the operator
            val = self.op(left, right, expression.operator)
            if val is not None:
                return val

            # If the operator is a boolean operator, handle it recursively
            if expression.operator in ["and", "or", "nor"]:
                if expression.operator == "and":
                    return left and right
                elif expression.operator == "or":
                    return left or right
                elif expression.operator == "nor":
                    return not left or not right
            else:
                raise MyntCompilerError(f"Unknown operator: {expression.operator}")
        else:
            # Return the value of an IdentifierNode
            return expression.value

    def validVariable(self, variable):
        if variable in map(lambda x: x["name"], self.myntjson["variables"]):
            return True
        return False

    # The first operator we see MUST not be "and" nor "or."
    def compile_condition(self, conditionNode: ExpressionNode, body) -> None:
        op = conditionNode.operator
        left = conditionNode.left
        right = conditionNode.right
        onlyNums = op in [">", "<", ">=", "<="]
        if op in [">", "<", ">=", "<=", "==", "!="]:
            if isinstance(left, IdentifierNode):
                if not self.validVariable(left.name):
                    raise MyntCompilerError(f"Variable {left.name} is not defined.")
                else:
                    # Should only be one match
                    var = list(filter(lambda x: x["name"] == left.name, self.myntjson["variables"]))[0]
                    if var["type"] != "number" and onlyNums:
                        raise MyntCompilerError(f"Variable {left.name} is not a number.")
                    data = var["data"]
                    result = self.evaluate(conditionNode)
                    print(result)

    
    def compile_function(self, functionNode: FunctionNode) -> None:
        flag = False
        if functionNode.name == "main":
            self.main = functionNode
            flag = True
        elif functionNode.name == "load":
            self.load = functionNode
            flag = True
        js = {}
        commands = []
        for statement in functionNode.body:
            if isinstance(statement, RunStatementNode):
                # Get the number value from statement.delay and separate it from the optional trailing 's' or 't'
                (delay, unit) = (statement.delay[:-1], statement.delay[-1]) if statement.delay[-1] in ['s', 't'] else (statement.delay, 't')
                command = fh.schedule(statement.function, delay, unit)
                commands.append(command)
                lgl(lgll.DEBUG, f"Added command: {command}")
            elif isinstance(statement, IfStatementNode):
                # Will have to get the condition and compile the child expressions until only a single left and right hand side exists,
                # then we will check that the operator is a valid operator and the value is a valid value,
                # then we will have to check if the condition is true or false and then compile the body of the if statement.
                # In order to test if the condition is true, we will need to see if the left hand side is a variable and if it is one
                # that is loaded in the scope of the program. If it is an unrecognized variable, we will have to throw an error.
                # If the left hand side is a number, we will have to check if the operator is a valid operator for numbers.
                # If the left hand side is a string, we will have to check if the operator is a valid operator for strings.
                # If the left hand side is a boolean, we will have to check if the operator is a valid operator for booleans.
                # If the left hand side is a variable and all checks have passed, and we have found the variable reference, then 
                # we will have to check the same way if the right hand side is a variable recognized in the scope.
                # Some variables may not be ones explicitly defined in the assignment statements, some may need to map to a dictionary of valid
                # variables and their values from the minecraft wiki.

                # Create an anonymous function with the body of the if statement
                t = self.compile_function(statement.then)

                # Return "if" part of the command
                c = self.compile_condition(statement.condition, t)
                # Return another command with negated condition c
                if statement.otherwise:
                    o = self.compile_function(statement.otherwise, t)
                    commands.append(o)
                commands.append(c)

            elif isinstance(statement, MCStatementNode):
                commands.append(statement.mcCommand)
                lgl(lgll.DEBUG, f"Added command: {statement.mcCommand}")
            else:
                raise Exception(f"Unknown statement type: {statement.type}")
        if flag:
            js = commands
            self.myntjson[functionNode.name] = js
        else:
            js["body"] = commands
            self.myntjson["functions"][functionNode.name] = js
        return commands
        

    def compile_assignment(self, assignmentNode):
        if isinstance(assignmentNode, AssignmentNode):
            var = {}
            data = None
            if assignmentNode.assignment.type == ASTNodeType.BLOCK:
                data = json.loads(assignmentNode.assignment.data)
            elif assignmentNode.assignment.type == ASTNodeType.NUMBER:
                data = assignmentNode.assignment.value
            elif assignmentNode.assignment.type == ASTNodeType.RESOURCE:
                data = assignmentNode.assignment.resource
            var["name"] = assignmentNode.variable
            var["type"] = assignmentNode.varType
            if assignmentNode.important:
                var["important"] = assignmentNode.important
            if data:
                var["data"] = data
            self.myntjson["variables"].append(var)
        else:
            raise Exception(f"Expected assignment node, received: {assignmentNode.type}")

    # Saves the compiled json file as "file-name"-mynt.json
    def saveJson(self):
        with open(f"{self.filename}-mynt.json", "w") as f:
            f.write(json.dumps(self.myntjson, indent=4))

    def compile(self):
        lgl(lgll.DEBUG, "Compiling Mynt program.")

        if "functions" not in self.myntjson:
            self.myntjson["functions"] = {}
        
        if "variables" not in self.myntjson:
            self.myntjson["variables"] = []

        if isinstance(self.ast, ProgramNode):
            statements = self.ast.statements
            # First pass, travel the tree and only compile variable assignments outside of functions.

            for statement in statements:
                if isinstance(statement, AssignmentNode):
                    lgl(lgll.DEBUG, f"Compiling assignment statement: [{statement.variable}]")
                    self.compile_assignment(statement)
                    statements.remove(statement)


            for statement in statements:
                if isinstance(statement, BlockNode):
                    lgl(lgll.DEBUG, f"Compiling function block: [{statement.name}]")
                    self.compile_function(statement)
                elif isinstance(statement, AssignmentNode):
                    lgl(lgll.DEBUG, f"Compiling assignment statement: [{statement.variable}]")
                    self.compile_assignment(statement)
                else:
                    raise Exception(f"Unknown statement type: {statement.type}")
        
        # Check if main and load are loaded
        if not self.main:
            raise MyntCompilerError("Main function not found")
        if not self.load:
            raise MyntCompilerError("Load function not found")

        self.saveJson()
        print(self.myntjson)