"""
    builtins.py

    Python source file declaring various standard FORTH methods that all FORTH capable
    systems should be equipped with.

    Copyright (c) 2016 Robert MacGregor
    This software is licensed under the MIT license. Refer to LICENSE.txt for
    more information.
"""

def strcat(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
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

def random(interp):
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

def mod(interp):
    rhs = int(interp.stack.pop())
    lhs = int(interp.stack.pop())
    interp.stack.append(lhs / rhs)

def store(interp):
    key = interp.stack.pop()
    value = interp.stack.pop()

    # First we look at locals, if its not there, just try to assign to globals
    if (key not in interp.local_variables):
        interp.global_variables[key] = value
    else:
        interp.local_variables[key] = value

def fetch(interp):
    key = interp.stack.pop()

    if (key not in interp.local_variables):
        interp.stack.append(interp.global_variables[key])
    else:
        interp.stack.append(interp.local_variables[key])

def jump(interp):
    offset = int(interp.stack.pop())
    interp.jump_target = interp.instruction_pointer + offset

def ifblock(interp):
    false_jump = int(interp.stack.pop())
    condition = int(interp.stack.pop())

    if (condition == 0):
        interp.jump_target = interp.instruction_pointer + false_jump

        #print(interp.codeblock.payload[interp.instru])

def equals(interp):
    rhs = interp.stack.pop()
    lhs = interp.stack.pop()
    interp.stack.append(int(rhs == lhs))

def print_stack(interp):
    print(interp.stack)

def nop(interp):
    pass
