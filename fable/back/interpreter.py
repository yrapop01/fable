from pprint import pprint
import traceback
import code
import ast
import _ast
import json
import re
import sys
import io
from fable import fab

def save_last_expr(code, var):
    try:
        tree = ast.parse(code)
        if not tree.body or not isinstance(tree.body[-1], _ast.Expr):
            return code, False

        row = tree.body[-1].lineno - 1
        col = tree.body[-1].col_offset
        lines = code.splitlines()
        lines[row] = lines[row][:col] + var + '=' + lines[row][col:]

        return '\n'.join(lines), True
    except Exception:
        traceback.print_exc()
        return code, False

def print_exc():
    inf = sys.exc_info()
    lines = traceback.format_exception(*inf)
    del lines[1]
    print(''.join(lines), end='', file=sys.stderr)

def print_val(value):
    if value is None:
        return

    with io.StringIO() as f:
        pprint(value, stream=f)
        print(f.getvalue(), end='')

class Interpreter:
    def __init__(self, files, log):
        self.files = files
        self.log = log
        self.var = {}

    def _compile_and_run(self, code, filename):
        try:
            c = compile(code, filename, mode='exec')
            exec(c, self.var, self.var)
        except Exception:
            print_exc()
        except KeyboardInterrupt:
            print_exc()

    def run(self, code, filename='cell'):
        code, expr = save_last_expr(code, '__fable_expr__')
        if expr:
            self.var['__fable_expr__'] = None

        try:
            sys.stdin = self.files[0]
            sys.stdout = self.files[1]
            sys.stderr = self.files[2]
            fab.htmlout = self.files[3]

            self._compile_and_run(code, filename)
            if expr:
                print_val(self.var['__fable_expr__'])
        finally:
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
            sys.stdin = sys.__stdin__
            fab.htmlout = fab.__htmlout__
