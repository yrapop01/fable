import json
import asyncio
import logging
import websockets
from datetime import datetime
from fable.utils.logger import log
from fable.back.shell import acquire, release

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

async def run_code(shell, ids, code, delay=1):
    try:
        async with shell.lock:
            await shell.run(code)
            ended = False
            while not ended:
                message, ended = await shell.readout()
                await send(shell.user, 'out', {'ids': ids, 'messages': [message]})

    except Exception as e:
        _log.exception(e)

async def main(ws):
    shell = None
    await send(ws, 'opened')
    try:
        while True:
            action, value = await recv(ws)
            if action == 'notebook':
                shell = await acquire(value['name'], ws,
                                      force=value.get('force', False))
                if shell is None:
                    _log.error('could not acquire the shell')
                    await send(ws, ['error', 'the notebook is busy'])
            elif action == 'run':
                ids = value['ids']
                code = value['code']
                asyncio.ensure_future(run_code(shell, ids, code))
            elif action == 'interrupt':
                shell.interrupt()
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        _log.exception(e)
        raise
    finally:
        await release(shell, ws)
