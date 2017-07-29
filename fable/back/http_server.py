import os
import glob
from sanic import Sanic
from fable.back.end import main
from fable import front
from fable import config

app = Sanic()

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

@app.websocket(config.root + '/conn')
async def serve(request, ws):
    await main(ws)

def run():
    add_static(app, config.root, os.path.dirname(front.__file__))
    app.run(host=config.host, port=config.port)
    
if __name__ == '__main__':
    run()
