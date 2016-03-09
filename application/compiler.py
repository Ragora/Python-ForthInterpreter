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

class CodeBlock(object):
    name = None
    payload = None

    global_variables = None
    """
        A list of all global variables declared on this specific codeblock.
    """

    local_variables = None
    """
        A list of all local variables declared on this specific codeblock.
    """

    def __init__(self, name, payload):
        self.name = name
        self.payload = payload

class Compiler(object):
    _comment_regex = re.compile("\\(.*?\\)", re.DOTALL)
    _string_regex = re.compile("\".*?\"")

    def __init__(self):
        pass

    def compile_muf(self, payload):
        result = [ ]

        # Any header bits in our input?
        header_end = payload.find(":")
        header_payload = payload[0:header_end].rstrip()

        global_variables = [ ]
        local_variables = [ ]
        if (header_payload != ""):
            headers = header_payload.split("\n")

            for header in headers:
                header_payload = header.split()
                variable_type = header_payload[0]
                variable_name = header_payload[1]

                if (variable_type == "lvar"):
                    local_variables.append(variable_name)
                else:
                    global_variables.append(variable_name)

        payload = payload[header_end + 1:]
        payload = self._first_stage(payload)

        name = payload[0][1:].strip()
        payload = payload[1:]
        if (payload.pop() != ";"):
            print("ERROR")

        payload = self._second_stage(payload)
        payload = self._third_stage(payload)

        result = CodeBlock(name, payload)
        result.local_variables = local_variables
        result.global_variables = global_variables
        return result

    def _third_stage(self, payload):
        """
            In the third stage, we massage the conditions into something the
            interpreter readily works with while also verifying that they're
            property closed with a 'then' clause.
        """

        # Our program should be symmetrical: if, else and then counts should be equal
        if (not (payload.count("if") == payload.count("then") or payload.count("if") == payload.count("else"))):
            return

        # Process for every if in the payload
        try:
            current_if = payload.index("if")

            while (True):
                else_start = -1
                then_start = -1

                for iteration in range(current_if + 1, len(payload)):
                    # We may cover multiple else's in a layered structure
                    if (payload[iteration] == "else" and else_start == -1):
                        else_start = iteration
                    elif (payload[iteration] == "then"):
                        then_start = iteration
                        break

                # Failed to figure out where these are
                if (else_start == -1):
                    print("Failed to find else")
                    return
                elif (then_start == -1):
                    print("Failed to find then")
                    return

                # Remove the then clause by replacing with a nop
                payload[then_start] = "nop"

                # Where are our offsets?
                then_offset = then_start - current_if
                else_offset = else_start - current_if

                # First, we overwrite the else with a jump
                payload[else_start] = "jump"

                # Write the jump payloads to offset the else and the then blocks by +2
                payload.insert(else_start, str(then_offset + 1))
                payload.insert(current_if, str(else_offset + 2))

                # Loop foreach jump below us and correct their jump offsets by +2
                for iteration in range(then_offset + 1, len(payload)):
                    command = payload[iteration]
                    if (command == "jump"):
                        target_index = iteration - 1
                        old_offset = int(payload[target_index])
                        new_offset = int(payload[iteration - 1]) + 2

                        payload[target_index] = str(new_offset)

                current_if = payload.index("if", current_if + 3)
        except ValueError:
            pass

        return payload

    def _second_stage(self, payload):
        """
            In the second stage we try to sort out multiple commands per index
            so that the code is fully serial from top to bottom with no extra
            checking involved for the compiler.
        """

        result = [ ]
        for line in payload:
            # We can match at any position in the string, so we store matches and their locations
            matches = { }
            for string_match in re.finditer(self._string_regex, line):
                string_text = string_match.group(0)
                string_length = len(string_text)
                string_start = string_match.start(0)
                string_end = string_match.end(0)

                # First modify any indices that come after us to be pos - length, we use this to order things correctly
                current_matches = dict(matches)
                for next_location in current_matches:
                    next_text = matches[next_location]
                    matches.remove(next_location)
                    matches[next_location - string_length] = next_text

                matches[string_start - 1] = string_text[1:len(string_text) - 1]
                line = line[0:string_start] + line[string_end + 1:len(line)]

            # Now we process foreach word
            line = line.strip()

            if (line != ""):
                pointer = 0
                words = line.split()

                #print(matches)
                for word in words:
                    if (pointer in matches):
                        matches[pointer + 1] = word
                    else:
                        matches[pointer] = word

                    pointer = pointer + len(word)

            # Now we build our lines
            lines = [ ]

            match_locations = matches.keys()
            match_locations.sort()
            for match_location in match_locations:
                lines.append(matches[match_location])
            result.extend(lines)

        return result

    def _first_stage(self, payload):
        """
            The first stage of our compilation process strips off commenting
            and massages the data down to a list of at least 1 command per index
            and may also contain portions of strings that span multiple indices.
            It is the job of stage two to sort these out.
        """
        payload = re.sub(self._comment_regex, "", payload)

        # Now we remove the various spaces floating around
        payload = payload.replace("\r", "")
        payload = payload.split("\n")

        result = [ ]
        for line in payload:
            line = line.strip().rstrip()

            if (line != ""):
                result.append(line)

        return result
