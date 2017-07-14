import os
from sanic import Sanic
from fable.back.end import main
from fable import front

app = Sanic()
app.static('/', os.path.dirname(front.__file__))

@app.websocket('/')
async def serve(request, ws):
    await main(ws)

if __name__ == '__main__':
    app.run()
