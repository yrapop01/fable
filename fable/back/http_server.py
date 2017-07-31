import os
import glob
from fable.back.end import main
from fable import front
from fable import config
from fable.utils.logger import log, nullStreamHandler
from sanic import Sanic
from sanic import log as sanic_log

_app = Sanic()
_log = log(__name__)

def add_static(app, root, path):
    extensions = {'png', 'woff', 'woff2', 'css', 'map', 'js', 'html', 'ico', 'eot', 'ttf', 'svg'}
    files = glob.glob(os.path.join(path, '**'), recursive=True)
    files = [(filename, filename[len(path)+1:]) for filename in files]
    for filename in files:
        if filename[0].rsplit('.', 2)[-1] not in extensions:
            continue
        app.static(root + '/' + filename[1], filename[0])
        if filename[1] == 'index.html':
            app.static(root + '/', filename[0])

@_app.websocket(config.root + '/conn')
async def serve(request, ws):
    await main(ws)

@_app.listener('after_server_start')
def after_start(app, loop):
    url = 'http://{0}:{1}/{2}'.format(config.host, config.port, config.root)
    _log.info('Started Fable on address ' + url)

def disable_sanic_logs():
    sanic_log.log.handlers = []
    sanic_log.netlog.handlers = []

def run():
    add_static(_app, config.root, os.path.dirname(front.__file__))
    disable_sanic_logs()
    _app.run(host=config.host, port=config.port, log_config=None)
    
if __name__ == '__main__':
    run()
