"""
    interpreter.py

    Python source file declaring the FORTH interpreter class along with its
    various exception types.

    Copyright (c) 2016 Robert MacGregor
    This software is licensed under the MIT license. Refer to LICENSE.txt for
    more information.
"""

import os
import sys
import random
import traceback

import compiler
import builtins

class InterpreterError(StandardError):
    pass

class InterpreterTypeError(InterpreterError):
    pass

class InterpreterRuntimeError(InterpreterError):
    """
        An exception class representing an exception raised by the FORTH interpreter,
        typically at some point during runtime when a fatal condition is encountered.
    """

    interpreter = None
    """
        The interpreter in question that's gone to crap.
    """

    reason = None
    """
        The exception thrown by Python to trigger this interpreter error to be
        raised.
    """

    def __init__(self, interpreter, reason, info):
        self.interpreter = interpreter
        self.reason = reason

        exc_type, exc_obj, traceback = info
        self.exc_type = exc_type
        self.exc_obj = exc_obj
        self.traceback = traceback

    def __str__(self):
        # Produce frame snapshots
        snapshots = ""
        for index, snapshot in enumerate(self.interpreter.frame_snapshots):
            stack, pointer = snapshot

            if pointer < 0 or pointer >= len(self.interpreter.callable.payload):
                pointer = "%u <Out of Bounds>" % pointer
            else:
                pointer = "%u (%s)" % (pointer, self.interpreter.callable.payload[pointer])

            snapshots = "%s\n        Frame %u, EIP %s %s" % (snapshots, index, pointer, stack)

        # Build a program disassembly
        disassembly = self.interpreter.callable.disassemble()

        output = """

        The FORTH interpreter encountered a fatal error and could not continue.
        Reason: %s

        Interpreter Stack: %s
        Instruction Pointer: %u
        Stack Frame Shapshots:
        %s

        Program Length: %u
        Program Disassembly:
        %s

        """ % (repr(self.reason), self.interpreter.stack, self.interpreter.instruction_pointer, snapshots,
        len(self.interpreter.callable.payload), disassembly)

        return output

class Interpreter(object):
    commands = None
    """
        A dictionary of command names to python methods accepting a stack state.
        Alternatively, the mapped value may be a codeblock to execute some more
        interpreted FORTH instead. Each interpreter has its own command list as
        the command list may be manually extended post initialization for customization.
    """

    stack = None
    """
        The current stack state of the FORTH interpreter.
    """

    global_variables = None
    local_variables = None

    callable = None
    """
        The callable in use by this interpreter.
    """

    instruction_pointer = None
    """
        The current instruction pointer of the interpreter. This should not be
        written directly as unintended behavior may occur. Please use jump_target
        instead if you desire to modify this at run time. If this is ever False,
        the interpreter will perform a successful exit.
    """

    jump_target = None
    """
        An absolute instruction pointer that the interpreter will jump to upon
        the next available cycle.
    """

    command_maximum = 200
    """
        What the upper limit on FORTH command counts should be for this interpreter
        to prevent infinite loops. Make this 0 for no maximum.
    """

    command_count = None
    """
        The current count of FORTH commands executed by this interpreter from a given
        execute method.
    """

    loop_starts = []
    """
        The starting indices in loops that our program has to keep track of.
    """

    stack_debug = True
    frame_snapshots = None

    def __init__(self):
        self.commands = { }
        self.init_builtin_commands()

        self.stack = []
        self.global_variables = { }

    def execute(self, callable):
        """
            Executes the given FORTH callable produced by the compiler.
        """
        if (type(callable) is not compiler.Callable):
            raise InterpreterTypeError("Cannot use non-Callable types with execute!")

        self.callable = callable
        self.local_variables = { }
        self.instruction_pointer = 0
        self.command_count = 0
        self.frame_snapshots = [ ]

        try:
            while self.instruction_pointer < len(self.callable.payload):
                if (self.stack_debug is True):
                    self.frame_snapshots.append((list(self.stack), self.instruction_pointer))

                # Read the next operation to perform
                operation = self.callable.payload[self.instruction_pointer]

                # If it is a special type, append the payload
                if type(operation) is compiler.CodeString or type(operation) is compiler.CodeNumber:
                    self.stack.append(operation.data)
                else:
                    self.commands[operation](self)

                # Exit execution
                if self.instruction_pointer is False:
                    break

                # Perform a jump if instructed to
                if (self.jump_target is not None):
                    self.instruction_pointer = self.jump_target
                    self.jump_target = None
                else:
                    self.instruction_pointer = self.instruction_pointer + 1

                if (self.command_count >= self.command_maximum and self.command_maximum > 0):
                    print("Terminated: Maximum of %u commands exceeded." % self.command_maximum)
                    return

                self.command_count = self.command_count + 1
        except StandardError as e:
            print(traceback.format_exc())
            exc_type, exc_obj, exc_tb = sys.exc_info()
            raise InterpreterRuntimeError(self, e, (exc_type, exc_obj, exc_tb))

        self.callable = None

    def init_builtin_commands(self):
        """
            Initializes the standardized FORTH command list for the interpreter
            to refer to when dispatching calls.
        """
        self.commands["strcat"] = builtins.strcat
        self.commands["swap"] = builtins.swap
        self.commands["pop"] = builtins.pop
        self.commands["dup"] = builtins.dup
        self.commands["random"] = builtins.randint

        # Arithmetic
        self.commands["+"] = builtins.add
        self.commands["-"] = builtins.sub
        self.commands["*"] = builtins.mult
        self.commands["/"] = builtins.div
        self.commands["%"] = builtins.mod

        # Stack manipulations
        self.commands["over"] = builtins.over

        # Bitwise
        self.commands["rot"] = builtins.rot

        # Comparisons
        self.commands["<"] = builtins.less_than
        self.commands[">"] = builtins.greater_than
        self.commands[">="] = builtins.less_than_equal
        self.commands["<="] = builtins.greater_than_equal

        # Control flow
        self.commands["="] = builtins.equals
        self.commands["if"] = builtins.ifblock
        self.commands["jump"] = builtins.jump
        self.commands["not"] = builtins.not_command
        self.commands["exit"] = builtins.exit
        self.commands["else"] = builtins.elseblock

        # Looping
        self.commands["begin"] = builtins.begin
        self.commands["until"] = builtins.until
        self.commands["while"] = builtins.whileblock
        self.commands["repeat"] = builtins.repeat

        # Variables
        self.commands["!"] = builtins.store
        self.commands["@"] = builtins.fetch

        # Etc
        self.commands["name"] = lambda interp: interp.stack.append("Test")

        # Debug
        self.commands["print"] = builtins.println
        self.commands["_stack"] = builtins.print_stack
        self.commands["nop"] = builtins.nop
        self.commands[";"] = builtins.nop
        self.commands["then"] = builtins.nop
