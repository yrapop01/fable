from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from fable import config
from fable import script
import os
import sys
import json
import traceback
import base64

class Events(WebSocket):
    on_close = []

    def handleMessage(self):
        try:
            try:
                filename, arguments, preamble, body = json.loads(self.data)
            except ValueError:
                print('Less than 3 lines in data', file=sys.stderr)
                return

            if not arguments:
                print('Empty instruction', file=sys.stderr)
                return

            command = arguments[0]
            if command not in {'run', 'save', 'load', 'bibl'}:
                print('Uknown command', command, file=sys.stderr)
                return

            name = os.path.basename(filename)
            home = os.path.expanduser(config.home)
            path = os.path.join(home, name)

            if command == 'load':
                response = {'header': 'load', 'contents': script.load(path)}
                self.sendMessage(json.dumps(response))
                return

            if command == 'save':
                script.save(path, preamble, body)
                return

            if command == 'bibl':
                if config.bibl:
                    if config.bibl[0] == '/':
                        bpath = config.bibl
                    else:
                        bpath = os.path.join(home, config.bibl)
                    with open(bpath) as f:
                        bibliography = f.read()
                else:
                    bibliography = ''

                response = {'header': 'bibl', 'body': bibliography}
                self.sendMessage(json.dumps(response))
                return

            if command == 'run':
                if len(arguments) < 2:
                    print('Missing entry id in run command', file=sys.stderr)
                    return
                entry_id = arguments[1]
                pdf, errors, is_small = script.run(preamble, body)
                b64 = base64.b64encode(pdf).decode()
                body = {'pdf': b64, 'errors': errors, 'is_small': is_small}
                response = {'header': 'pdf', 'id': entry_id, 'body': body}
                self.sendMessage(json.dumps(response))
        except Exception:
            traceback.print_exc()

    def handleConnected(self):
        pass

    def handleClose(self):
        for handler in Events.on_close:
            handler()

class Server:
    def __init__(self):
        self.server = SimpleWebSocketServer(config.host, config.port, Events)
        self.sockname = self.server.serversocket.getsockname()

    def __call__(self):
        self.server.serveforever()

def run():
    try:
        server = Server()
        print(f'Starting server: host {server.sockname[0]}, port {server.sockname[1]}', flush=True)
        server()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run()
