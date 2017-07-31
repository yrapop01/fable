import traceback
import logging
import sys

class Log:
    def prn(self, msg):
        f = self.f if self.f else sys.stdout
        print(msg, file=f, flush=True)
    def exception(self, e):
        traceback.print_exc()
    debug = error = info = warning = prn

class DevNull(object):
    def pass_func(self, *args, **kw):
        pass
    def __getattr__(self, attr):
        return self.pass_func

def log(name, filename=''):
    log = Log()
    if filename: 
        log.f = open(filename, 'wt')
    else:
        log.f = None
    return log

def nullStreamHandler():
    return logging.StreamHandler(DevNull())


