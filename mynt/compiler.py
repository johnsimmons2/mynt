from mynt.parser import ASTNode, ASTNodeType, AssignmentNode, BlockNode, MCStatementNode, MyntError, ProgramNode, FunctionNode, RunStatementNode, IfStatementNode
from mynt.logging import Logger, LogLevel
import mynt.funchelper as fh

lgl = Logger.log
lgll = LogLevel

class MyntCompilerError(MyntError):
    def __init__(self, message):
        super().__init__(message)

class Compiler:
    def __init__(self, ast):
        self.ast = ast
        self.main = None
        self.load = None
        self.myntjson = {}
    
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
                pass
            elif isinstance(statement, MCStatementNode):
                commands.append(statement.mcCommand)
                lgl(lgll.DEBUG, f"Added command: {statement.mcCommand}")
            else:
                raise Exception(f"Unknown statement type: {statement.type}")
        if flag:
            js = commands
        else:
            js["body"] = commands
        self.myntjson[functionNode.name] = js
        

    def compile_assignment(self, assignmentNode):
        pass

    def compile(self):
        lgl(lgll.DEBUG, "Compiling Mynt program.")
        if isinstance(self.ast, ProgramNode):
            statements = self.ast.statements
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


        print(self.myntjson)