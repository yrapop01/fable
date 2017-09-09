import os
import sys
import json
import signal
import argparse

from fable.back.interpreter import Interpreter
from fable.back.repl_proto import Events, encode, decode
from fable.logs import log

_log = log('repl')

class IO:
    def __init__(self, inp, out):
        self.inp = inp
        self.out = out

    def write(self, event, data, urgent=False):
        _log.debug('Writing', event, data)
        _log.debug('Length', event, len(data))
        print(encode(event, data), file=self.out, flush=urgent)

    def read(self, size=-1):
        print(encode(Event.INP), file=self.out, flush=True)
        return decode(self.inp.readline())

    def flush(self):
        self.out.flush()

class WriterWrapper:
    def __init__(self, out, prefix):
        self.out = out
        self.prefix = prefix

    def flush(self):
        self.out.flush()

    def write(self, data):
        self.out.write(self.prefix, data)

def fork():
    if os.name != 'posix':
        return -1
    
    pid = os.fork()
    if pid < 0:
        return -1

    if pid > 0:
        return pid

    # child
    os.setsid()
    
    received = signal.sigwait([signal.SIGUSR1])
    if received != signal.SIGUSR1:
        sys.exit(os.EX_OK)

    return 0

def _noop(sig, frame):
    _log.debug('SIGINT received and ignored')

def _send_noint():
    # Send no interrupts request and expect to get an ack

    s = signal.getsignal(signal.SIGINT)
    try:
        signal.signal(signal.SIGINT, _noop)

        print(encode(Events.NOINT), flush=True)
        key, _ = decode(next(sys.stdin))

        assert key == Events.NOINT
    finally:
        signal.signal(signal.SIGINT, s)

def run(interp, code):
    try:
        print(encode(Events.STARTED), flush=True)
        interp.run(code)
        _send_noint()
    except KeyboardInterrupt:
        # At most one keyboard interrupt is promised to be sent after STARTED
        # (and 0 before STARTED)
        pass

    print(encode(Events.DONE), flush=True)

def repl():
    io = IO(sys.stdin, sys.stdout)
    files = [io, WriterWrapper(io, Events.OUT), WriterWrapper(io, Events.ERR), WriterWrapper(io, Events.HTML)]
    interpreter = Interpreter(files, _log)

    for line in sys.stdin:
        event, code = decode(line)

        if event == Events.RUN:
            run(interpreter, code)
        elif event == Events.PATH:
            interpreter.change_path(json.loads(code))
        elif event == Events.PING:
            print(encode(Events.PONG), flush=True)
        elif event == Events.FORK:
            pid = fork()
            print(encode(Events.FORKED, str(pid)), flush=True)
        else:
            print(encode(Events.EXC, 'Unkown event %s' % event), flush=True)

if __name__ == "__main__":
    try:
        repl()
    except (Exception, BaseException):
        _log.exception()
