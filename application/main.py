import string

import compiler
import interpreter

class Application(object):
    def main(self):
        with open("test.txt") as handle:
            instance = compiler.Compiler()
            block = instance.compile_muf(handle.read())

            interp = interpreter.Interpreter()
            #print(string.join(block.payload, "\n"))
            interp.execute(block)

            #print(interp.stack)
if __name__ == "__main__":
    Application().main()
