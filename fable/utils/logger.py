import traceback
import sys

class Log:
    def prn(self, msg):
        f = self.f if self.f else sys.stdout
        print(msg, file=f, flush=True)
    def exception(self, e):
        traceback.print_exc()
    debug = error = info = warning = prn

def log(name, filename=''):
    log = Log()
    if filename: 
        log.f = open(filename, 'wt')
    else:
        log.f = None
    return log
