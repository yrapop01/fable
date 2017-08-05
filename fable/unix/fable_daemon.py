import os
import sys
import json
import time
import signal
import psutil
import filelock
import webbrowser
from fable import config
from fable.back.http_server import run

def status():
    try:
        with open(config.INFO) as f:
            info = json.loads(f.read())
        if info['pid'] >= 0 and psutil.pid_exists(info['pid']):
            return info['pid'], info['url']
    except FileNotFoundError:
        pass
    return -1, -1

def print_status():
    with filelock.FileLock(config.LOCK):
        pid, url = status()
    if pid < 0:
        print('No running Fable processes found')
    else:
        print('Fable runs: pid', pid, 'url', url)

def start():
    os.makedirs(config.FOLD, exist_ok=True)
    with filelock.FileLock(config.LOCK):
        pid, url = status()
        if pid >= 0:
            print('Fable already runs (pid ' + str(pid) + ') on address', url)
            return
        with open(config.INFO, 'w') as f:
            link = 'http://{0}:{1}/{2}'.format(config.host, config.port, config.root)
            f.write(json.dumps({'pid': os.getpid(), 'url': link}))

    try:
        run()
    finally:
        with filelock.FileLock(config.LOCK):
            os.remove(config.INFO)

def stop():
    os.makedirs(config.FOLD, exist_ok=True)
    with filelock.FileLock(config.LOCK):
        pid, _ = status()

        if pid < 0:
            print('Warning: no running Fable processes found')
            return
            
        try:
            print('Sstoping term signal to (pid ' + str(pid) + ')')
            os.kill(pid, signal.SIGINT)
        except OSError:
            pass

    for w in [0, 1, 4]:
        time.sleep(w)
        if not psutil.pid_exists(pid):
            return
    print('Could not stop Fable (pid ' + str(pid) + ') on port', port)

def open_browser():
    with filelock.FileLock(config.LOCK):
        pid, url = status()
    if pid < 0:
        print('No running Fable processes found')
    else:
        url = url.replace('0.0.0.0', 'localhost')
        webbrowser.open_new_tab(url)

def spawnDaemon(func):
    # From: https://stackoverflow.com/questions/6011235/run-a-program-from-python-and-have-it-continue-to-run-after-the-script-is-kille
    # do the UNIX double-fork magic, see Stevens' "Advanced Programming in the UNIX Environment" for details (ISBN 0201563177)
    try: 
        pid = os.fork() 
        if pid > 0:
            # parent process, return and keep running
            return
    except OSError as e:
        print("fork #1 failed: %d (%s)" % (e.errno, e.strerror), file=sys.stderr)
        sys.exit(1)

    os.setsid()

    # do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent
            sys.exit(0) 
    except OSError as e:
        print("fork #2 failed: %d (%s)" % (e.errno, e.strerror), file=sys.stderr)
        sys.exit(1)

    # do stuff
    func()

    # all done
    os._exit(os.EX_OK)

def main():
    choices = ('start', 'stop', 'status', 'browser')
    if len(sys.argv) < 2 or sys.argv[1] not in choices:
        print('Usage:', sys.argv[0], '|'.join(choices) + ' [port Number] [host Number] [root String]')
        return

    if sys.argv[1] == 'start':
        spawnDaemon(start)
    elif sys.argv[1] == 'status':
        print_status()
    elif sys.argv[1] == 'browser':
        open_browser()
    elif sys.argv[1] == 'stop':
        stop()


if __name__ == "__main__":
    main()
