import aiofiles
import json
from fable.utils.logger import log
from fable.back.repl_proto import Events

class Cell:
    def __init__(self, guid, index, kind='', data='', out=()):
        self.guid = guid
        self.index = index
        self.kind = kind
        self.data = data
        self.out = list(out)

    def as_dict(self):
        return {'guid': self.guid,
                'kind': self.kind,
                'data': self.data,
                'out': self.out}

class Notebook:
    def __init__(self, filename='', cells=(), running='', path=()):
        self.filename = filename
        self.slow_cells = list(cells)
        self.fast_cells = {c.guid: c for c in cells}
        self.detached = (filename == '')
        self.path = dict(path)
        self.running = running

    def detach(self):
        self.detached = True

    def newcell(self, old_guid, new_guid):
        index = self.fast_cells[old_guid].index + 1 if old_guid is not None else 0
        cell = Cell(new_guid, index=index)

        self.slow_cells.insert(index, cell)
        self.fast_cells[new_guid] = cell

    def remove(self, guid):
        assert guid != self.running, "Cannot remove running cell"

        cell = self.fast_cells[guid]
            
        self.slow_cells.pop(cell.index)
        del self.fast_cells[guid]

        return cell
    
    def move_up(self, guid):
        cell = self.fast_cells[guid]
        assert cell.index > 0, "Cannot move up the first cell"

        self.slow_cells.remove(cell.index)
        self.slow_cells.insert(cell.index - 1)

    def move_down(self, guid):
        cell = self.fast_cells[guid]
        assert cell.index < len(self.slow_cells) - 1, "Cannot move down the last cell"

        self.slow_cells.remove(cell.index)
        self.slow_cells.insert(cell.index + 1)

    def change(self, guid, data):
        cell = self.fast_cells[guid]
        new_kind = None

        kind = detect_kind(data)
        if kind != cell.kind:
            cell.kind = kind
            new_kind = kind

        cell.data = data
        return new_kind

    def change_path(self, path):
        self.path = path

    def cells(self):
        return self.slow_cells

    def cells_dict(self):
        return [cell.as_dict() for cell in self.slow_cells]

    def messages(self):
        while self.msgs:
            yield self.msgs.pop()

    def write(self, guid, message):
        event, data = message

        if event == Events.STARTED:
            assert not self.running, "Cannot run two cells together"
            cell = self.fast_cells[guid]
            self.running = guid
            cell.out = []
        elif event == Events.DONE:
            self.running = ''
        else:
            cell = self.fast_cells[guid]
            cell.out.append(message)

    def restart(self):
        self.running = ''

    def kind(self, guid):
        return self.fast_cells[guid].kind

def loads(data, filename):
    data = json.loads(data)

    version = data['version'];
    assert version == '1.0', 'Bad notebook version'

    cells = data['cells']
    for i, cell in enumerate(cells):
        cell['index'] = i
    cells = [Cell(**cell) for cell in cells]

    running = data['running']

    return Notebook(filename, cells, running)

def dumps(notebook):
    cells = [cell.as_dict() for cell in notebook.cells()]

    data = {'version': '1.0', 'cells': cells, 'running': notebook.running}
    return json.dumps(data)

async def load(filename, detached=False):
    try:
        async with aiofiles.open(filename) as f:
            notebook = loads(await f.read(), filename)
        if detached:
            notebook.detach()
        return notebook
    except FileNotFoundError:
        return Notebook(filename)

async def save(notebook):
    if not notebook.detached:
        async with aiofiles.open(notebook.filename, mode='w') as f:
            await f.write(dumps(notebook))

def detect_kind(data):
    if data.startswith('\\'):
        return 'tex'
    return 'python'
