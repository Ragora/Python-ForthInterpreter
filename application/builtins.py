"""
    builtins.py

    Python source file declaring various standard FORTH methods that all FORTH capable
    systems should be equipped with.

    Copyright (c) 2016 Robert MacGregor
    This software is licensed under the MIT license. Refer to LICENSE.txt for
    more information.
"""

import struct
import random

def strcat(interp):
    """
        strcat operator takes the two values at the top of the stack and concatenates them as a string.

        FIXME: Should we convert non-str types when doing the concat or throw an error?
    """

    rhs = str(interp.stack.pop())
    lhs = str(interp.stack.pop())
    interp.stack.append(lhs + rhs)

def swap(interp):
    """
        Swap operator swaps the two elements at the top of the stack.
    """

    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs)
    interp.stack.append(lhs)

def pop(interp):
    """
        Pop operator pops the element from the top of the stack, throwing it away.
    """

    interp.stack.pop()

def dup(interp):
    """
        Dup operator duplicates the element at the top of the stack, pushing a copy.
    """

    interp.stack.append(interp.stack[len(interp.stack) - 1])

def randint(interp):
    """
        Implementation for the 'random' operator returns a random integer to the top of the
        stack.
    """

    interp.stack.append(struct.unpack("<L", random._urandom(4))[0])

def add(interp):
    """
        Performs the following operation and replaces the top two stack elements
        with the result of:
            stack[n] + stack[n-1]
    """

    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs + rhs)

def sub(interp):
    """
        Performs the following operation and replaces the top two stack elements
        with the result of:
            stack[n] - stack[n-1]
    """

    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs - rhs)

def mult(interp):
    """
        Performs the following operation and replaces the top two stack elements
        with the result of:
            stack[n] * stack[n-1]
    """

    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs * rhs)

def div(interp):
    """
        Performs the following operation and replaces the top two stack elements
        with the result of:
            stack[n] / stack[n-1]
    """

    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs / rhs)

def println(interp):
    """
        Prints whatever is currently at the top of the stack to the console.
    """

    print(interp.stack.pop())

def mod(interp):
    """
        Performs modulus on the top two stack elements and pushes the result to the
        stack.
    """

    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs % rhs)

def store(interp):
    """
        The store operator (!) will take a key, value pair at the top of the stack
        and store them as a variable association to be later grabbed with the fetch
        operator.
    """

    key = interp.stack.pop()
    value = interp.stack.pop()

    # First we look at locals, if its not there, just try to assign to globals
    if key not in interp.local_variables:
        interp.global_variables[key] = value
    else:
        interp.local_variables[key] = value

def fetch(interp):
    """
        The fetch operator (@) will look up a variable going by the name of whatever
        is currently at the top of the stack and push its value to the stack.
    """

    key = interp.stack.pop()

    if key not in interp.local_variables:
        interp.stack.append(interp.global_variables[key])
    else:
        interp.stack.append(interp.local_variables[key])

def jump(interp):
    """
        The jump operator instructs the interpreter to perform a relative jump from the current
        instruction to elsewhere in the program.
    """

    offset = int(interp.stack.pop())
    interp.jump_target = interp.instruction_pointer + offset

def ifblock(interp):
    """
        The if operator takes the top of the stack and evaluates it as a boolean, executing
        a certain codepath if it happens to be true. A different codepath if false and there
        is an 'else' operation.

        FIXME: This will jump to the wrong locations if we have nested if's
    """

    condition = bool(interp.stack.pop())

    # Jump to the else or the then
    if condition is False:
        jump_offset = 0

        remaining_operations = interp.callable.payload[interp.instruction_pointer:]

        try:
            else_offset = remaining_operations.index("else")
        except ValueError:
            else_offset = None

        try:
            then_offset = remaining_operations.index("then")
        except ValueError:
            then_offset = None

        if else_offset is not None and then_offset is not None and else_offset < then_offset:
            jump_offset = else_offset + 1
        elif else_offset is not None and then_offset is not None and then_offset < else_offset:
            jump_offset = then_offset + 1

        interp.jump_target = interp.instruction_pointer + jump_offset

def elseblock(interp):
    """
        The else operator is implemented as a handle for an if's true codepath only
        to handle jumping over the false codepath.
    """

    remaining_operations = interp.callable.payload[interp.instruction_pointer:]
    then_offset = remaining_operations.index("then")
    interp.jump_target = interp.instruction_pointer + (then_offset + 1)

def equals(interp):
    """
        Performs the following check and replaces the top two stack elements
        with the result of:
            stack[n] == stack[n-1]
    """

    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs == lhs)

def greater_than(interp):
    """
        Performs the following check and replaces the top two stack elements
        with the result of:
            stack[n] > stack[n-1]
    """

    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs > lhs)

def greater_than_equal(interp):
    """
        Performs the following check and replaces the top two stack elements
        with the result of:
            stack[n] >= stack[n-1]
    """

    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs >= lhs)

def less_than(interp):
    """
        Performs the following check and replaces the top two stack elements
        with the result of:
            stack[n] < stack[n-1]
    """

    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs < lhs)

def less_than_equal(interp):
    """
        Performs the following check and replaces the top two stack elements
        with the result of:
            stack[n] <= stack[n-1]
    """

    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs <= lhs)

def begin(interp):
    """
        The begin operation begins a loop.
    """

    interp.loop_starts.append(interp.instruction_pointer + 1)

def until(interp):
    """
        The until operation exits the loop if the loop condition is met. Otherwise, it will jump
        back to the start of the loop for another run.
    """

    condition = bool(interp.stack.pop())

    if condition:
        interp.loop_starts.pop()
    else:
        interp.jump_target = interp.loop_starts[len(interp.loop_starts) - 1]

def print_stack(interp):
    """
        The _stack operation prints the entire stack contents to the console.
    """

    print(interp.stack)

def not_command(interp):
    """
        The not operation does a boolean NOT operation on the element at the top of the
        stack.
    """

    interp.stack.append(not bool(interp.stack.pop()))

def over(interp):
    """
        The over command takes a copy of the top stack element and leapfrogs it
        over the element currently behind.
    """

    # FIXME: This is potentially not fully implemented correctly
    top_value = interp.stack[len(interp.stack) - 1]
    interp.stack = [top_value] + interp.stack

def nop(interp):
    """
        Do nothing.
    """

    pass

def rot(interp):
    """
        The rot operation rotates the top two stack elements.
    """

    # FIXME: This is potentially not fully implemented correctly
    if len(interp.stack) < 2:
        return

    rhs = interp.stack.pop()
    lhs = interp.stack.pop()

    interp.stack.append(rhs)
    interp.stack.append(lhs)

def exit(interp):
    """
        The exit command exits execution of the program entirely.
    """

    interp.instruction_pointer = False

def whileblock(interp):
    """
        The while block exits the loop if our exit condition is met.
    """

    top = bool(interp.stack.pop())

    if top:
        remaining_operations = interp.callable.payload[interp.instruction_pointer:]
        then_offset = remaining_operations.index("then")
        interp.jump_target = interp.instruction_pointer + (then_offset + 1)

def repeat(interp):
    """
        The repeat operation jumps back to the beginning of the loop we are currently in.
    """

    interp.jump_target = interp.loop_starts[len(interp.loop_starts) - 1]
