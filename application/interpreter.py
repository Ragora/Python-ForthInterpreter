"""
    interpreter.py

    Python source file declaring the FORTH interpreter class along with its
    various exception types.

    Copyright (c) 2016 Robert MacGregor
    This software is licensed under the MIT license. Refer to LICENSE.txt for
    more information.
"""

import random
import struct

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

    def __init__(self, interpreter, reason):
        self.interpreter = interpreter
        self.reason = reason

    def __str__(self):
        # Produce frame snapshots
        snapshots = ""
        for index, snapshot in enumerate(self.interpreter.frame_snapshots):
            stack, pointer = snapshot

            if pointer < 0 or pointer >= len(self.interpreter.codeblock.payload):
                pointer = "%u <Out of Bounds>" % pointer
            else:
                pointer = "%u (%s)" % (pointer, self.interpreter.codeblock.payload[pointer])

            snapshots = "%s\n        Frame %u, EIP %s %s" % (snapshots, index, pointer, stack)

        # Build a program disassembly
        disassembly = ""
        for command in self.interpreter.codeblock.payload:
            disassembly = "%s\n        %s" % (disassembly, command)

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

        """ % (self.reason, self.interpreter.stack, self.interpreter.instruction_pointer, snapshots,
        len(self.interpreter.codeblock.payload), disassembly)

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

    codeblock = None
    """
        The codeblock in use by this interpreter.
    """

    instruction_pointer = None
    """
        The current instruction pointer of the interpreter. This should not be
        written directly as unintended behavior may occur. Please use jump_target
        instead if you desire to modify this at run time.
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

    stack_debug = True
    frame_snapshots = None

    def __init__(self):
        self.commands = { }
        self.init_builtin_commands()

        self.global_variables = { }

    def execute(self, codeblock):
        """
            Executes the given FORTH codeblock produced by the compiler.
        """
        if (type(codeblock) is not compiler.CodeBlock):
            raise InterpreterTypeError("Cannot use non-Codeblock types with execute!")

        self.stack = [ ]
        self.codeblock = codeblock
        self.local_variables = { }
        self.instruction_pointer = 0
        self.command_count = 0
        self.frame_snapshots = [ ]

        try:
            while (self.instruction_pointer < len(self.codeblock.payload)):
                if (self.jump_target is not None):
                    self.instruction_pointer = self.jump_target
                    self.jump_target = None

                if (self.stack_debug is True):
                    self.frame_snapshots.append((self.stack, self.instruction_pointer))
                    print("EIP %u (%s): %s" % (self.instruction_pointer, self.codeblock.payload[self.instruction_pointer], self.stack))

                line = self.codeblock.payload[self.instruction_pointer]
                if (line not in self.commands):
                    self.stack.append(line)
                else:
                    self.commands[line](self)

                self.instruction_pointer = self.instruction_pointer + 1
                if (self.command_count >= self.command_maximum and self.command_maximum > 0):
                    print("Terminated: Maximum of %u commands exceeded." % self.command_maximum)
                    return
                self.command_count = self.command_count + 1
        except StandardError as e:
            raise InterpreterRuntimeError(self, e)

        self.codeblock = None

    def init_builtin_commands(self):
        """
            Initializes the standardized FORTH command list for the interpreter
            to refer to when dispatching calls.
        """
        self.commands["strcat"] = builtins.strcat
        self.commands["swap"] = builtins.swap
        self.commands["pop"] = builtins.pop
        self.commands["dup"] = builtins.dup
        self.commands["random"] = builtins.random

        # Arithmetic
        self.commands["+"] = builtins.add
        self.commands["*"] = builtins.mult
        self.commands["/"] = builtins.div
        self.commands["%"] = builtins.mod

        # Control flow
        self.commands["="] = builtins.equals
        self.commands["if"] = builtins.ifblock
        self.commands["jump"] = builtins.jump

        # Variables
        self.commands["!"] = builtins.store
        self.commands["@"] = builtins.fetch

        # Debug
        self.commands["_stack"] = builtins.print_stack
        self.commands["nop"] = builtins.nop
