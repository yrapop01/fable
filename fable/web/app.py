import webbrowser
import pathlib
import urllib
import os
import argparse

from fable import config
from fable.web.server import Server, Events

def open_url(url):
    webbrowser.open_new_tab(url)

def exit():
    print('Fable: shutting down the server', flush=True)
    os._exit(0)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    for key in config.VALUES:
        parser.add_argument('--' + key)

    args = parser.parse_args()

    server = Server()
    Events.on_close.append(exit)
    port = server.sockname[1]

    basename = os.path.basename(args.filename)
    fullname = os.path.join(os.path.expanduser(config.home), basename)

    directory = pathlib.Path(__file__).parent.absolute()
    query = urllib.parse.urlencode({'port': port, 'filename': basename})

    url = f'file://{directory}/page.html?' + query
    print(f'Fable: opening {fullname} in web browser', flush=True)
    open_url(url)
    print('Fable: starting the server', flush=True)
    server()

if __name__ == "__main__":
    run()
