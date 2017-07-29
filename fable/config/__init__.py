import os
import sys
import configparser

HOME = os.path.expanduser('~')
CONF = os.path.join(HOME, '.fable', 'fable.conf')

VALUES = {
    'port': 0,
    'host': '127.0.0.1',
    'root': ''
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
        if key in VALUES.keys():
            VALUES[key] = value

def assign_values():
    module = sys.modules[__name__]
    for key, value in VALUES.items():
        module.__dict__[key] = value

load_config(CONF)
load_args()
assign_values()

if __name__ == "__main__":
    print(VALUES)
