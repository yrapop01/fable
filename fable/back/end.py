import json
import asyncio
import logging
import websockets
from datetime import datetime
from fable.utils.logger import log
from fable.back.shell import acquire, release, abandon
from fable.back import notebook
from fable.back import minitex

_log = log(__name__)

async def send(ws, code, data=''):
    if not ws:
        _log.error('Cannot send: web socket is None')
        return
    if not ws.open:
        _log.error('Cannot send: web socket is not open')
        return
    try:
        message = json.dumps({'code': code, 'value': data})
        await ws.send(message)
    except Exception as e:
        _log.exception(e)

async def recv(ws):
    data = await ws.recv()
    action, value = json.loads(data)
    return action, value

async def run_code(shell, ids, code, doc):
    try:
        await shell.run(code)
        ended = False
        while not ended:
            message, ended = await shell.readout()
            async with shell.run_msg_lock():
                doc.write(ids, message)
                await notebook.save(doc)
                await send(shell.user, 'code_run', {'ids': ids, 'msg': [message]})
    except Exception as e:
        await send(shell.user, 'code_run_error', {'ids': ids, 'error': str(e)})
        _log.exception(e)

async def run_tex(ws, shell, guid, code, doc):
    path, messages = minitex.parse(code, doc.path)

    await shell.change_path(json.dumps(doc.path))

    doc.change_path(path)
    for message in messages:
        doc.write(guid, message)
    await notebook.save(doc)

    await send(ws, 'code_run', {'ids': guid, 'msg': messages})

async def run_cell(ws, shell, ids, code, doc):
    kind = doc.kind(ids)
    if kind == 'tex':
        await run_tex(ws, shell, ids, code, doc)
    else:
        asyncio.ensure_future(run_code(shell, ids, code, doc))

async def init(ws, name, force=False, detached=False):
    shell = await acquire(name, ws, force='force')

    if shell is None:
        _log.error('could not acquire the shell')
        await send(ws, ['error', 'the notebook is busy'])
        return None, None

    if name == '':
        doc = notebook.Notebook()
        desc = {'version': '1.0', 'running': '', 'cells': []}
        await send(ws, 'opened', desc)
        return shell, doc

    async with shell.run_msg_lock():
        shell.show()
        doc = await notebook.load(name, detached)
        desc = {'version': '1.0', 'running': doc.running, 'cells': doc.cells_dict()}
        await send(ws, 'opened', desc)

    return shell, doc

async def main(ws):
    shell = None
    doc = None
    try:
        while True:
            action, value = await recv(ws)
            if action == 'notebook':
                assert shell is None and doc is None
                shell, doc = await init(ws, value['name'],
                                        value.get('force', False),
                                        value.get('detached', False))
            elif action == 'run':
                await run_cell(ws, shell, value['ids'], value['code'], doc)
            elif action == 'interrupt':
                await shell.interrupt()
            elif action == 'restart':
                doc.restart()
                await shell.restart()
                await notebook.save(doc)
            elif action == 'newcell':
                doc.newcell(value['prev_id'], value['cell_id'])
                await notebook.save(doc)
            elif action == 'change':
                new_kind = doc.change(value['guid'], value['code'])
                if new_kind is not None:
                    await send(ws, 'kind_changed', {'guid': value['guid'], 'kind': new_kind})
                await notebook.save(doc)
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        _log.exception(e)
        raise
    finally:
        await release(shell, ws)

def bye():
    abandon()
