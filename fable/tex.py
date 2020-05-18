import os
import json
import shutil
import tempfile
import subprocess
from fable import config
import pygments

MAGIC = "%FABLEMAGIC"
PREFIX = '\n%FABLE:'
HEADER = PREFIX + 'NEXT!\n'

class NotBalanced(Exception):
    pass

def split_escaped(data):
    if not data.startswith(MAGIC + HEADER):
        return [data]

    entries = data.split(HEADER)[1:]
    undo_escape = [entry.replace(PREFIX + PREFIX, PREFIX) for entry in entries]

    return undo_escape

def split_unescaped(data):
    lengths, content = data.split('\n', maxsplit=1)

    fables = []
    cumsum = 0
    ns = [int(s) for s in lengths.split(',')]
    for n in ns:
        fables.append(content[cumsum:cumsum + n])
        cumsum += n

    return fables

def load(path):
    try:
        with open(path, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        return []
    
    return split_escaped(data)

def save(path, data):
    fables = split_unescaped(data)

    body = MAGIC
    for fable in fables:
        body += HEADER + fable.replace(PREFIX, PREFIX + PREFIX)

    with open(path, 'w') as f:
        f.write(body)

def reduce_packages(body):
    packages = []

    for line in body.splitlines():
        if line.startswith('\\usepackage'):
            packages.append(line)

    return packages

def reduce_commands(body):
    groups = group_pipeline(token_pipeline(body))
    commands = []

    KEEP = {'setcopyright', 'acmYear', 'acmDOI', 'acmConference',
            'acmBooktitle', 'acmPrice', 'acmISBN', 'author', 'email', 'newcommand',
            'renewcommand', 'AtBeginDocument', 'endinput', 'ccsdesc', 'keywords', 'title'}

    ENVIR = {'abstract'}

    for group in groups:
        if group[0].startswith('\\') and group[0][1:] in KEEP:
            commands.append(''.join(group))
        if len(group) > 2 and group[0] == '\\begin' and group[1][0] == '{' and group[1][-1] == '}' and group[1][1:-1] in ENVIR:
            commands.append(''.join(group))

    return commands

def comments(s):
    comment = False
    for c in s:
        if c == '%':
            comment = True
        if not comment:
            yield c
        if c == '\n':
            comment = False

def macros(s):
    name = ''
    for c in s:
        if not name and c != '\\':
            yield c
            continue
        if name == '\\' and (c == '\\' or c in '{}<>|'):
            yield name + c
            name = ''
            continue
        if name and c.isalpha():
            name += c
            continue
        if name:
            yield name
            name = ''
        if c == '\\':
            name = c
        else:
            yield c
    if name:
        yield name

def brackets(INC, DEC):
    def match(s):
        name = ''
        count = 0
        for c in s:
            if name:
                name += c
                if c == DEC:
                    count -= 1
                    if count == 0:
                        yield name
                        name = ''
                if c == INC:
                    count += 1
                continue
            if not name and c == INC:
                count += 1
                name = c
                continue
            yield c

    return match

curly = brackets('{', '}')
square = brackets('[', ']')

def filt_tokens(tokens, s):
    for c in s:
        if c in tokens:
            continue
        yield c

def verb(s):
    token = ''
    prev = ''
    for c in s:
        if prev == '\\verb':
            token = prev + c
            prev = ''
            continue
        if not token:
            if prev:
                yield prev
            prev = c
            continue
        if c == '|':
            yield token + c
            token = ''
            continue
        token += c

    assert not token and prev != '\\verb'
    yield prev

def join_commands(s):
    prev = ''
    opt = []
    req = []
    for c in s:
        if len(prev) > 1 and prev[0] == '\\' and prev[1].isalpha():
            if len(c) >= 2 and c[0] == '{' and c[-1] == '}':
                req.append(c)
                continue
            if len(req) == 0 and len(c) >= 2 and c[0] == '[' and c[-1] == ']':
                opt.append(c)
                continue

            yield [prev] + opt + req
            prev = c
            opt = []
            req = []
            continue

        if prev:
            yield [prev]
        prev = c
    if prev:
        yield [prev] + opt + req

def newcommand(s):
    prev = []
    for c in s:
        if prev and prev[0] in {'\\newcommand' or '\\renewcommand'}:
            yield prev + c
            prev = []
            continue
        if prev:
            yield prev
        prev = c
    if prev:
        yield prev

def join_envirs(s):
    envir = []
    count = 0

    for c in s:
        if c[0] == '\\begin':
            envir.extend(c)
            count += 1
            continue
        if count > 0:
            envir.extend(c)
            if c[0] == '\\end':
                count -= 1
                if count == 0:
                    yield envir
                    envir = []
            continue
        yield c

def token_pipeline(body):
    return filt_tokens({'\\begin{document}', '\\end{document}'}, square(curly(verb(macros(comments(body))))))

def group_pipeline(tokens):
    return join_envirs(newcommand(join_commands(tokens)))

def is_blank(body):
    envirs = group_pipeline(token_pipeline(body))

    SKIP_ENVIR = ['CCSXML', 'abstract']
    SKIP_CMD = {'documentclass', 'setcopyright', 'acmYear', 'acmDOI', 'acmConference',
                'acmBooktitle', 'acmPrice', 'acmISBN', 'author', 'email', 'newcommand',
                'renewcommand', 'AtBeginDocument', 'endinput', 'ccsdesc', 'keywords',
                'title', 'usepackage', 'fxsetup'}
    for env in envirs:
        if len(env) > 2 and env[0] == '\\begin' and env[1][0] == '{' and env[1][-1] == '}' and env[1][1:-1] in SKIP_ENVIR:
            continue
        if env[0].startswith('\\') and env[0][1:] in SKIP_CMD:
            continue
        if all(not s.strip() for s in env):
            continue
        return False

    return True

def run(data, entry_index):
    entries = split_unescaped(data)
    packages = ['\\usepackage{fancyvrb}', '\\usepackage{color}']
    commands = []

    for i, contents in enumerate(entries):
        if i == entry_index:
            if is_blank(contents):
                return b'', ''
            return render_standalone(packages, commands, contents)
        packages += reduce_packages(contents)
        commands += reduce_commands(contents)

    raise Exception(f'Entry with id {entry_id} was not found')

class PersistentDirectory:
    def __init__(self, *args, **kw):
        self.fullpath = tempfile.mkdtemp(*args, **kw)

    def __enter__(self, *args, **kw):
        return self

    def __exit__(self, *args, **kw):
        return self

def tempdir(*args, delete=False, **kw):
    if delete:
        return tempfile.TemporaryDirectory(*args, **kw)
    return PersistentDirectory(*args, **kw)

def latex_errors(path):
    try:
        with open(path) as f:
            lines = f.read().splitlines()

        errors = []
        current = ''
        for line in lines:
            if line.startswith('!'):
                if line[-1] == '.':
                    errors.append(line)
                else:
                    current = line
                continue
            if current:
                current += ' ' + line
                if line.endswith('.'):
                    errors.append(current)
                    current = ''
        for error in errors:
            print(error, flush=True)
        return '\n'.join(errors)
    except FileNotFoundError:
        print('ERROR: LaTeX log file was not found', flush=True)
        return ''

def input_files(contents):
    INPUT = {'\\input', '\\includegraphics'}
    files = []

    try:
        commands = join_commands(token_pipeline(contents))
        for command in commands:
            if command[0] in INPUT:
                files.append(command[-1][1:-1])
    except Exception as ex:
        print(ex, flush=True)

    return files

def render_standalone(packages, commands, contents):
    text = STANDALONE.format(packages='\n'.join(packages),
                             commands='\n'.join(commands),
                             contents=contents)

    with tempdir(delete=False) as d:
        print('fullpath', d.fullpath)
        path = os.path.join(d.fullpath, 'text.tex')

        files = input_files(contents)

        with open(path, 'w') as f:
            f.write(text)

        if config.bibl:
            files.append(config.bibl)

        home = os.path.expanduser(config.home)
        for name in files:
            src = os.path.join(home, name)
            dst = os.path.join(d.fullpath, name)
            os.symlink(src, dst)
        try:
            subprocess.check_output([config.exec, '-interaction=batchmode', config.args, 'text.tex'], cwd=d.fullpath)
        except subprocess.CalledProcessError as ex:
            print('LaTeX returned non zero code', flush=True)
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
