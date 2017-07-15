import sys
import argparse
from threading import RLock

from fable.back.interpreter import Interpreter
from fable.back.repl_proto import Events, encode, decode
from fable.utils.logger import log

_log = log(__name__, '/tmp/fable.repl')

class IO:
    def __init__(self, inp, out):
        self.inp = inp
        self.out = out

    def write(self, event, data, urgent=False):
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

def run(interp, io, code):
    try:
        io.write(Events.STARTED, '', urgent=True)
        interp.run(code)
    except KeyboardInterrupt:
        _log.info('Got interrupt request')
    finally:
        _log.info('OUT0')
        io.write(Events.DONE, '', urgent=True)
        _log.info('OUT1')

def repl():
    io = IO(sys.stdin, sys.stdout)
    files = [io, WriterWrapper(io, Events.OUT), WriterWrapper(io, Events.ERR)]
    interpreter = Interpreter(files, WriterWrapper(io, Events.HTML), _log)

    for line in sys.stdin:
        event, code = decode(line)

        if event == Events.RUN:
            run(interpreter, io, code)
            _log.info('RUN DONE')
        elif event == Events.PING:
            print(encode(Events.PONG), flush=True)
        else:
            print(encode(Events.EXC, 'Unkown event %s' % event), flush=True)

if __name__ == "__main__":
    repl()
