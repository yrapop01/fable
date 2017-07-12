from sanic import Sanic
from back.end import main

app = Sanic()
app.static('/', 'front/')

@app.websocket('/')
async def serve(request, ws):
    await main(ws)

if __name__ == '__main__':
    app.run()
