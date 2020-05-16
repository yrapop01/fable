class Events:
    # REPL to USER EVENTS
    INP = 'inp'
    OUT = 'out'
    ERR = 'err'
    HTML = 'html'
    EXC = 'exc'
    PONG = 'pong'
    PATH = 'path'
    DONE = 'ended'
    STARTED = 'started'
    FORKED = 'forked'

    # REPL <-> USER EVENTS
    NOINT = 'noint'

    # USER to REPL EVENTS
    WRT = 'wrt'
    RUN = 'run'
    PING = 'ping'
    FORK = 'fork'

def encode(event, data=''):
    return event + ' ' + data.replace('\n', '\\n')

def decode(message):
    msg = message.split(' ', 1)
    if len(msg) == 1:
        return msg[0].rstrip(), ''
    event, data = msg
    return event, data.replace('\\n', '\n')
