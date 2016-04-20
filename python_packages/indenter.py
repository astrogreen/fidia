import re
from collections import deque

class Indenter:

    def __init__(self, indent_size=2, enforce_spacing=True):
        self.code = ""
        self.indent_string = " " * indent_size
        self.enforce_spacing = enforce_spacing
        self.current_indent = deque()

    def add_line(self, code_line):
        self.add_many_lines(code_line)

    def _add_line(self, code_line):
        code_line = code_line.strip()
        if code_line == "":
            return
        indent_count = len(self.current_indent)
        if code_line[0] in ")}]":
            code_line = self.indent_string * (indent_count-1) + code_line
        else:
            code_line = self.indent_string * (indent_count) + code_line
        self._update_indent_with_string(code_line)
        self.code += code_line + "\n"

    def add_many_lines(self, code_lines):
        if self.enforce_spacing:
            code_lines_old = None
            while code_lines != code_lines_old:
                code_lines_old = code_lines
                # print(len(re.findall(r'([\n\A][\t ]*[^\t ]+[\t ]*)([\{\}\(\)\[\]])', code_lines)))
                # Add new lines to brackets that are not the first character of their line
                code_lines = re.sub(r'([^\t \n\A]+[ \t]*)([\{\}\(\)\[\]])', r'\1\n\2', code_lines)
                # Add new lines to brackets that are not the last character of their line
                code_lines = re.sub(r'([\{\}\(\)\[\]])([\t ]*[^\t \n\Z,]+)', r'\1\n\2', code_lines)
                # Add new lines between consecutive brackets
                code_lines = re.sub(r'([\{\}\(\)\[\]])([\{\}\(\)\[\]])', r'\1\n\2', code_lines)
        for line in code_lines.split("\n"):
            self._add_line(line)

    def del_chars(self, n_chars=1):
        # Check that the number of chars passed is sensible
        assert n_chars > 0
        # Check if the charachters removed will change the indents:
        self._update_indent_with_string(self.code[-(n_chars + 1):], reverse=True)
        # Remove the characters, (correctly accounting for the newline)
        self.code = self.code[:-(n_chars + 1)] + "\n"

    def _update_indent_with_string(self, code_line, reverse=False):
        if reverse:
            # When removing characters, we do not need to check for matching parens
            for char in reversed(code_line):
                if char in "({[]})":
                    assert self.current_indent.pop() == char
            return
        for char in code_line:
            if char in "({[":
                self.current_indent.append(char)
            elif char in ")}]":
                if len(self.current_indent) < 1:
                    raise Exception("Mis-matched parenthesis in last line above")
                last = self.current_indent.pop()
                if ((last == "(" and char == ")") or
                    (last == "{" and char == "}") or
                    (last == "[" and char == "]")):
                    pass
                else:
                    print(self.code, code_line)
                    raise Exception("Mis-matched parenthesis in last line above")
