import os
import json
import shutil
import tempfile
import traceback
import subprocess
from io import BytesIO
from PyPDF2 import PdfFileReader
from fable import config

MAGIC = "%FABLEMAGIC"
PREFIX = '\n%FABLE:'
HEADER = PREFIX + 'NEXT!\n'

TEX = '\n'.join("""
    \\def \\fable {{{version}}}
    \\def \\fabledir {{{path}}}

    {preamble}
    \\begin{{document}}
    {text}
    \\end{{document}}
""".lstrip().splitlines())
#.replace('{', '\\{').replace('}', '}}').replace('<', '{').replace('>', '}')

def split_escaped(data):
    if not data.startswith(MAGIC + HEADER):
        return ['', data]

    entries = data.split(HEADER)[1:]

    undo_escape = [entry.replace(PREFIX + PREFIX, PREFIX) for entry in entries]

    assert undo_escape[1].strip() == '\\begin{document}', undo_escape[1]
    assert undo_escape[-1].strip() == '\\end{document}', undo_escape[-1]

    preamble, body = undo_escape[0], undo_escape[2:-1]

    return [preamble, body]

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

def save(path, preamble, body):
    fables = split_unescaped(body)

    body = MAGIC 
    body += HEADER + preamble.replace(PREFIX, PREFIX + PREFIX)
    body += HEADER + '\\begin{document}'

    for fable in fables:
        body += HEADER + fable.replace(PREFIX, PREFIX + PREFIX)

    body += HEADER + '\\end{document}'

    with open(path, 'w') as f:
        f.write(body)

def is_small(pdf):
    if not pdf:
        return True

    with BytesIO(pdf) as f:
        reader = PdfFileReader(f)
        page = reader.getPage(0)
        return page.mediaBox.getWidth() < 25

def run(preamble, body):
    try:
        pdf, errors = render_standalone(preamble, body)
        return pdf, errors, is_small(pdf)
    except Exception as ex:
        print('Error:', ex)
        return b'', 'Fable:' + str(ex), False

class PersistentDirectory:
    def __init__(self, *args, **kw):
        self.fullpath = tempfile.mkdtemp(*args, **kw)

    def __enter__(self, *args, **kw):
        return self

    def __exit__(self, etype, value, tb):
        if etype:
            traceback.print_exception(etype, value, tb)
            raise value
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

def render_standalone(preamble, contents):
    with tempdir(delete=False) as d:
        path = os.path.join(d.fullpath, 'text.tex')
        text = TEX.format(version=config.VERSION,
                          path=d.fullpath,
                          preamble=preamble,
                          text=contents)
        print(path)
        with open(path, 'w') as f:
            f.write(text)

        home = os.path.expanduser(config.home)
        args = [config.exec, config.args] + ['-interaction=batchmode',
                f'-output-directory={d.fullpath}', path]
        try:
            subprocess.check_output(args, cwd=home)
        except subprocess.CalledProcessError as ex:
            print('LaTeX returned non zero code', flush=True)
            return b'', latex_errors(os.path.join(d.fullpath, 'text.log'))

        pdf = os.path.join(d.fullpath, 'text.pdf')
        with open(pdf, 'rb') as f:
            return f.read(), ''
