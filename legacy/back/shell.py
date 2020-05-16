import asyncio
import signal
import html
import sys
import os
from fable.back.repl_proto import Events, encode, decode
from fable.logs import log

_PYTHON = sys.executable
_REPL = os.path.join(*os.path.split(__file__)[:-1], 'repl.py')

_shells = {}
_glock = asyncio.Lock()

_log = log('backend')

class Shell:
    def __init__(self, name, user, buffsize=1024):
        self._proc = None
        self._user = user
        self._name = name
        self._hidden = False
        self._lock = asyncio.Lock()
        self._buff = b''

        # run state
        self._running = False
        self._interrupting = False
        self._nointerrupt = False

        # backup process
        self._backup_fork = -1

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
        await self.ping()

    async def ping(self):
        await self.writeline(Events.PING)
        _log.debug('ping sent')
        message, _ = await self.readline()
        _log.debug('ping reply', message)
        assert message == Events.PONG

    async def interrupt(self):
        async with self._lock:
            if not self._running:
                _log.error('Interrupting non running shell')
                return

            if self._interrupting:
                _log.error('Already interrupting')
                return

            if self._nointerrupt:
                _log.info('No interrupts stage')
                return

            self._interrupting = True
            os.kill(self._proc.pid, signal.SIGINT)

    async def unrun(self):
        if self._backup_fork < 0:
            await self.interrupt()
            return

        async with self._lock:
            if self._backup_fork < 0:
                _lof.info('Backup process dissapeared')
                return

            os.kill(self._proc.pid, signal.SIGTERM)
            os.kill(self._backup_fork, signal.SIGUSR1)

            self._proc.pid = self._backup_fork
            self._backup_fork = -1

    def run_msg_lock(self):
        return self._lock

    def stop(self):
        os.kill(self._proc.pid, signal.SIGTERM)

    async def restart(self):
        self.stop()
        await self.start()

    async def _backup_fork(self):
        await self.writeline(Events.FORK)
        event, data = await self.readline()
        assert event == Events.FORKED
        self._backup_pid = int(data)

    async def run(self, code):
        async with self._lock:
            assert not self._running
            self._running = True

        #await self._backup_fork()
        await self.writeline(Events.RUN, code)

    async def change_path(self, path):
        await self.writeline(Events.PATH, path)

    async def inp(self, code):
        await self.writeline(Events.INP, code)

    async def writeline(self, event, data=''):
        self._proc.stdin.write((encode(event, data) + '\n').encode('utf-8'))
        self._proc.stdin.drain()

    async def readline(self, n=2048):
        chunk = b''
        if b'\n' not in self._buff:
            while b'\n' not in chunk:
                chunk = await self._proc.stdout.read(n)
                if not chunk:
                    raise EOFError()
                self._buff += chunk

        i = self._buff.index(b'\n')
        line, self._buff = self._buff[:i], self._buff[i+1:]

        event, value = decode(line.decode('utf-8'))
        _log.debug('read line', event, value)
        return event, value
        
    async def readout(self, delay=1):
        try:
            event, data = await self.readline()
            if event == Events.NOINT:
                async with self._lock:
                    assert self._running
                    self._nointerrupt = True
                await self.writeline(Events.NOINT)
                event, data = await self.readline()
        except EOFError:
            # TODO: handle somehow (current state is wrong)
            return (Events.DONE, ''), True

        ended = (event == Events.DONE or event.endswith(Events.FORKED) and data == '0')
        if event in (Events.ERR, Events.OUT):
            data = html.escape(data)
        if ended:
            async with self._lock:
                assert self._running
                self._running = self._interrupting = self._nointerrupt =  False

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

def abandon():
    for shell in _shells.values():
        shell.stop()
