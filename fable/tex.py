import os
import json
import tempfile
import subprocess
from fable import config

class NotBalanced(Exception):
    pass

def split(data):
    entries = []
    sumlen = 0
    while data.startswith('%fable'):
        entry, data = data.split('\n', maxsplit=1)
        _, entry_id, entry_len_str = entry.split()
        entry_len = int(entry_len_str)
        entries.append((sumlen, entry_len, entry_id))
        sumlen += entry_len

    return entries, data

def fables(path):
    try:
        with open(path, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        return []
    
    entries, data = split(data)
    return [data[i:i + n] for i, n, _ in entries]

def save(path, data):
    with open(path, 'w') as f:
        f.write(data)

def reduce_packages(body):
    packages = []

    for line in body.splitlines():
        if line.startswith('\\usepackage'):
            packages.append(line)

    return packages

def reduce_commands(body):
    commands = []

    for line in body.splitlines():
        if line.startswith('\\newcommand') or line.startswith('\\renewcommand'):
            commands.append(line)

    return commands

def run(data, entry_id):
    entries, data = split(data)
    packages = []
    commands = []

    for i, n, _id in entries:
        contents = data[i:i + n]
        packages += reduce_packages(contents)
        commands += reduce_commands(contents)
        if entry_id == _id:
            return render_standalone(packages, commands, contents)

class PersistentTemporaryDirectory:
    def __init__(self, *args, **kw):
        self.fullpath = tempfile.mkdtemp(*args, **kw)

    def __enter__(self, *args, **kw):
        return self

    def __exit__(self, *args, **kw):
        return self

def latex_errors(path):
    try:
        with open(path) as f:
            lines = f.read().splitlines()

        errors = [line for line in lines if line.startswith('!')]
        for error in errors:
            print(error, flush=True)
        return '\n'.join(errors)
    except FileNotFoundError:
        print('ERROR: LaTeX log file was not found', flush=True)
        return ''

def render_standalone(packages, commands, contents):
    text = STANDALONE.format(packages='\n'.join(packages),
                             commands='\n'.join(commands),
                             contents=contents)

    with PersistentTemporaryDirectory() as d:
        path = os.path.join(d.fullpath, 'text.tex')

        with open(path, 'w') as f:
            f.write(text)

        try:
            subprocess.check_output([config.exec, '-interaction=batchmode', 'text.tex'], cwd=d.fullpath)
        except subprocess.CalledProcessError as ex:
            print('Error:', d.fullpath)
            return b'', latex_errors(os.path.join(d.fullpath, 'text.log'))

        pdf = os.path.join(d.fullpath, 'text.pdf')
        with open(pdf, 'rb') as f:
            return f.read(), ''

def _fix_template(template):
    opened = False
    for c in template.strip():
        if c == '@':
            yield '}' if opened else '{'
            opened = not opened
        elif c in '{}':
            yield c * 2
        else:
            yield c

def template(name):
    res = 'resources'
    loc = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    path = os.path.join(loc, res, name)
    with open(path) as f:
        return ''.join(_fix_template(f.read()))

STANDALONE = template('standalone.template.tex')
