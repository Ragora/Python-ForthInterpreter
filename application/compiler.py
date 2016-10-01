"""
    compiler.py

    Python source file declaring the FORTH compiler class along with its
    various exception types.

    Copyright (c) 2016 Robert MacGregor
    This software is licensed under the MIT license. Refer to LICENSE.txt for
    more information.
"""

import re
import string

class CompilerError(Exception):
    """
        Exception representing a compiler error.
    """

    pass

class CodeNumber(object):
    """
        A class representing a regular number in the FORTH program.
    """

    data = None
    """
        The raw number.
    """

    def __init__(self, number):
        self.data = number

    def __repr__(self):
        return "<CodeNumber %f>" % self.data

class CodeString(object):
    """
        A class representing a regular old string in the FORTH program.
    """

    data = None
    """
        The raw string data.
    """

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "<CodeString \"%s\">" % self.data

class Callable(object):
    """
        A class representing a callable block of FORTH code.
    """

    payload = None

    global_variables = None
    """
        A list of all global variables declared on this specific codeblock.
    """

    local_variables = None
    """
        A list of all local variables declared on this specific codeblock.
    """

    def disassemble(self):
        result = ""

        for op in self.payload:
            if type(op) is CodeString:
                result += "\t\"%s\"\n" % op.data
            elif type(op) is CodeNumber:
                result += "\t%f\n" % op.data
            else:
                result += "\t%s\n" % op

        return result

    def __init__(self, payload):
        self.payload = payload

class CodeBlock(object):
    """
        A class representing a fully compiled output.
    """

    callable_functions = None

    def __init__(self, callable_functions):
        self.callable_functions = callable_functions

    def disassemble(self):
        result = ""
        for callable_name in self.callable_functions:
            result += "Callable Function %s: \n" % callable_name
            result += self.callable_functions[callable_name].disassemble()
        return result

class Compiler(object):
    _comment_regex = re.compile("\\(.*?\\)", re.DOTALL)
    """
        A regular expression pattern representing a comment. This is simply used to strip
        out all commenting data as we don't need it.
    """

    _language_regex = re.compile(":.+|[\"]([^\"])+[\"]| *\S+ *")
    """
        A regular expression representing a token in the FORTH language. This is used to locate
        all meaningful symbols within our input buffer.
    """

    def __init__(self):
        pass

    def get_tokens(self, input):
        """
            A list of lists where the second layer of lists is the token content that appeared on each
            line from the top of the input buffer to the bottom.

            :parameters:
                input - The input string.
        """

        output = []
        input = re.sub(self._comment_regex, "", input)
        input = input.rstrip().lstrip()

        lines = input.split("\n")
        for index, line in enumerate(lines):
            line = line.rstrip().lstrip()

            if line == "":
                continue

            line_data = {"text": line, "tokens": []}

            # For each matching token, record the start and end positions as well as line
            for match in re.finditer(self._language_regex, line):
                token_data = {"line": index + 1, "start": match.start(), "end": match.end(), "text": match.group(0).lstrip().rstrip()}
                line_data["tokens"].append(token_data)

            output.append(line_data)

        return output

    def collapse_tokens(self, input):
        """
            Collapses the line delineated list of tokens down to a long list of tokens to process.

            :parameters:
                input - The input line data to process.
        """

        result = []
        for line in input:
            result += line["tokens"]
        return result

    def syntax_analysis(self, tokens):
        """
            Performs a syntax analysis on the input FORTH, ensuring that the syntax is correct.

            :parameters:
                tokens - The input tokens to process.
        """

        processed_code_block = False

        def throw_error(error_message, token):
            """
                Helper function to throw an error with some useful information including visually where the problem lies.

                :parameters:
                    error_message - The message to throw.
                    token - The offending token.
            """
            highlight_text = ""

            for iteration in range(len(error_message) + token["start"]):
                highlight_text += " "
            highlight_text += "^"
            error_message += line_data["text"]

            helper_text = "The Error is Here---"
            if len(helper_text) < len(highlight_text):
                text_data = list(highlight_text)

                start_index = (len(highlight_text) - 1) - len(helper_text)
                for index, character in enumerate(helper_text):
                    text_data[start_index + index] = character

                highlight_text = "".join(text_data)

            raise CompilerError("\n%s\n%s" % (error_message, highlight_text))

        for line_data in tokens:
            for token in line_data["tokens"]:
                # If we're not processing a code block and our current token isn't one, we have an issue
                if processed_code_block is False and token["text"][0] != ":":
                    throw_error("Began FORTH programming, but no code block was declared on line %u, character %u: " % (token["line"], token["start"]), token)

                # If we passed the above check, then we're good on code blocks
                processed_code_block = True

                # Any tokens with " at the beginning or end should be complete
                token_end = len(token["text"]) - 1
                if (token["text"][0] == "\"" and token["text"][token_end] != "\"") or (token["text"][token_end] == "\"" and token["text"][0] != "\""):
                    throw_error("Found incomplete string on line %u, character %u: " % (token["line"], token["start"]), token)

    def lexical_analysis(self, tokens):
        """
            Performs a lexical analysis on the input tokens. This is used to ensure that the program actually makes sense once it is verified to be syntactically
            correct.
        """

        pass

    def build_result(self, tokens):
        """
            Builds the final codeblock containing callable functions.

            :parameters:
                tokens - The input tokens.
        """

        result = {}
        callable_data = None

        current_callable_name = None
        for token_data in tokens:
            if token_data["text"][0] == ":":
                current_callable_name = token_data["text"][1:].rstrip().lstrip()

                if callable_data is not None:
                    result[current_callable_name] = Callable(callable_data)

                callable_data = []
            else:
                token_text = token_data["text"]
                token_index_last = len(token_text) - 1

                # If it is a number, add it as a codenumber
                try:
                    callable_data.append(CodeNumber(float(token_text)))
                    continue
                except ValueError:
                    pass

                if token_text[0] == "\"" and token_text[token_index_last] == "\"":
                    callable_data.append(CodeString(token_text.rstrip("\"").lstrip("\"")))
                else:
                    callable_data.append(token_text)

        if current_callable_name is not None and callable_data is not None and len(callable_data) != 0:
            result[current_callable_name] = Callable(callable_data)

        return CodeBlock(result)

    def compile_forth(self, payload):
        """
            Builds the input FORTH into a usable interpreted sequence.

            :parameters:
                payload - The input string.
        """

        tokens = self.get_tokens(payload)
        self.syntax_analysis(tokens)
        self.lexical_analysis(tokens)

        tokens = self.collapse_tokens(tokens)
        return self.build_result(tokens)
