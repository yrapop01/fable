import os
import sys
import json

HOME = os.path.join(os.path.expanduser('~'), '.config')
FOLD = os.path.join(HOME, 'fable')
CONF = os.path.join(FOLD, 'conf.json')

VALUES = {
    'port': 4891,
    'host': '127.0.0.1',
    'home': os.getcwd(),
    'exec': 'xelatex',
    'bibl': '',
    'args': '-shell-escape'
}

def load_config(path):
    try:
        with open(path) as f:
            conf = json.load(f)
        for key in conf:
            if key in VALUES:
                VALUES[key] = conf[key]
            else:
                print('Unrecognized configuration key', key, flush=True)
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
