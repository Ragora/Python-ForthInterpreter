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
    rhs = str(interp.stack.pop())
    lhs = str(interp.stack.pop())
    interp.stack.append(lhs + rhs)

def swap(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs)
    interp.stack.append(lhs)

def pop(interp):
    interp.stack.pop()

def dup(interp):
    interp.stack.append(interp.stack[len(interp.stack) - 1])

def randint(interp):
    interp.stack.append(struct.unpack("<L", random._urandom(4))[0])

def add(interp):
    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs + rhs)

def sub(interp):
    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs - rhs)

def mult(interp):
    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs * rhs)

def div(interp):
    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs / rhs)

def println(interp):
    print(interp.stack.pop())

def mod(interp):
    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs % rhs)

def store(interp):
    key = interp.stack.pop()
    value = interp.stack.pop()

    # First we look at locals, if its not there, just try to assign to globals
    if key not in interp.local_variables:
        interp.global_variables[key] = value
    else:
        interp.local_variables[key] = value

def fetch(interp):
    key = interp.stack.pop()

    if key not in interp.local_variables:
        interp.stack.append(interp.global_variables[key])
    else:
        interp.stack.append(interp.local_variables[key])

def jump(interp):
    offset = int(interp.stack.pop())
    interp.jump_target = interp.instruction_pointer + offset

def ifblock(interp):
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
    jump_offset = 0

    remaining_operations = interp.callable.payload[interp.instruction_pointer:]

    then_offset = remaining_operations.index("then")
    jump_offset = then_offset + 1
    interp.jump_target = interp.instruction_pointer + jump_offset

def equals(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs == lhs)

def greater_than(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs > lhs)

def less_than(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs < lhs)

def greater_than_equal(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs >= lhs)

def less_than_equal(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(rhs <= lhs)

def begin(interp):
    interp.loop_starts.append(interp.instruction_pointer + 1)

def until(interp):
    condition = bool(interp.stack.pop())

    if condition:
        interp.loop_starts.pop()
    else:
        interp.jump_target = interp.loop_starts[len(interp.loop_starts) - 1]

def print_stack(interp):
    print(interp.stack)

def not_command(interp):
    interp.stack.append(not bool(interp.stack.pop()))

def over(interp):
    # FIXME: This is potentially not fully implemented correctly
    top_value = interp.stack[len(interp.stack) - 1]
    interp.stack = [top_value] + interp.stack

def nop(interp):
    pass

def rot(interp):
    # FIXME: This is potentially not fully implemented correctly
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()

    interp.stack.append(rhs)
    interp.stack.append(lhs)

def exit(interp):
    interp.instruction_pointer = False
