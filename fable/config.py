import os
import sys
import configparser

HOME = os.path.join(os.path.expanduser('~'), '.config')
FOLD = os.path.join(HOME, 'fable')
CONF = os.path.join(FOLD, 'fable.conf')
INFO = os.path.join(FOLD, 'fable.info')
LOCK = os.path.join(FOLD, 'fable.lock')
LOGS = os.path.join(FOLD, 'logs')

VALUES = {
    'port': 4891,
    'host': '127.0.0.1',
    'home': '~',
    'exec': 'xelatex'
}

def load_config(path):
    try:
        parser = configparser.ConfigParser()
        parser.read(path)
        for key in VALUES.keys():
            if key in parser:
                VALUES[key] = parser[key]
    except FileNotFoundError:
        pass

def load_args():
    for key, value in zip(sys.argv[1:-1], sys.argv[2:]):
        if key.startswith('--'):
            key = key[2:]
            if key in VALUES:
                create_value = type(VALUES[key])
                VALUES[key] = create_value(value)

def assign_values():
    module = sys.modules[__name__]
    for key, value in VALUES.items():
        module.__dict__[key] = value

load_config(CONF)
load_args()
assign_values()

if __name__ == "__main__":
    print(VALUES)
