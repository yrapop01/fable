import traceback

class Log:
    def prn(self, msg):
        print(msg, flush=True)
    def exception(self, e):
        traceback.print_exc()
    debug = error = info = warning = prn

def log(name):
    return Log()
