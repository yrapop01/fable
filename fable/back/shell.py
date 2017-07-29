import asyncio
import signal
import html
import sys
import os
from fable.back.repl_proto import Events, encode, decode
from fable.utils.logger import log

_PYTHON = sys.executable
_REPL = os.path.join(*os.path.split(__file__)[:-1], 'repl.py')

_shells = {}
_glock = asyncio.Lock()

_log = log(__name__)

class Shell:
    def __init__(self, name, user, buffsize=1024):
        self._proc = None
        self._user = user
        self._name = name
        self._hidden = False
        self._running = False
        self._lock = asyncio.Lock()

    def assign(self, user, force=False):
        if self.user == user:
            _log.warning('nothing to assign')
            return True
        if not force and not self.available:
            _log.error('shell is busy')
            return False

        _log.info('assigning shell' if user is not None else 'releasing shell')
        self._user = user
        self._hidden = True
        return True

    def show(self):
        self._hidden = False

    async def start(self):
        files = dict(stdin=asyncio.subprocess.PIPE,
                     stdout=asyncio.subprocess.PIPE,
                     stderr=asyncio.subprocess.DEVNULL)
        self._proc = await asyncio.create_subprocess_exec(_PYTHON, _REPL, **files)
        ping = await self.ping()
        assert ping

    async def ping(self):
        await self.writeline(Events.PING)
        message, _ = await self.readline()
        return message == Events.PONG

    async def interrupt(self):
        async with self._lock:
            if self._running:
                os.kill(self._proc.pid, signal.SIGINT)
            else:
                _log.error('Interrupting non running shell')

    def run_msg_lock(self):
        return self._lock

    def stop(self):
        os.kill(self._proc.pid, signal.SIGTERM)

    async def restart(self):
        self.stop()
        await self.start()

    async def run(self, code):
        async with self._lock:
            assert not self._running
            self._running = True
           
        await self.writeline(Events.RUN, code)

    async def change_path(self, path):
        await self.writeline(Events.PATH, path)

    async def inp(self, code):
        await self.writeline(Events.INP, code)

    async def writeline(self, event, data=''):
        self._proc.stdin.write((encode(event, data) + '\n').encode('utf-8'))
        self._proc.stdin.drain()

    async def readline(self):
        line = await self._proc.stdout.readline()
        if not line:
            raise EOFError()
        if line.endswith(b'\n'):
            line = line[:-1]

        event, value = decode(line.decode('utf-8'))
        return event, value

    async def readout(self, delay=1):
        event, data = await self.readline()

        ended = (event == Events.DONE)
        if event in (Events.ERR, Events.OUT):
            data = html.escape(data)
        if ended:
            async with self._lock:
                assert self._running
                self._running = False

        return (event, data), ended

    @property
    def name(self):
        return self._name

    @property
    def user(self):
        if self._hidden:
            return None
        return self._user

    @property
    def available(self):
        return self._user is None or not self._user.open

async def acquire(name, user, force=False):
    _log.debug('trying to acquire shell named "' + name + '"')
    assert user is not None

    if name:
        async with _glock:
            if name in _shells:
                shell = _shells[name]
                if shell.assign(user, force):
                    return shell
                return None
            else:
                shell = _shells[name] = Shell(name, user)
    else:
        _log.debug('Creating anonymous shell')
        shell = Shell(name, user)

    await shell.start()
    return shell

async def release(shell, user):
    if shell is None:
        return
    if not shell.name:
        shell.stop()
        return
    async with _glock:
        if shell.user == user:
            shell.assign(None, force=True)

async def stop(name):
    shell = _shells[name]
    async with _glock:
        del _shells[name]

    shell.stop()
