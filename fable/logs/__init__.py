import traceback
import logging
import sys
import os
from fable import config

def log(name):
    log = logging.getLogger(name)

    log.propagate = False
    log.handlers = []

    log.addHandler(handler(name))
    #log.setLevel(logging.DEBUG)

    return log

def handler(name):
    os.makedirs(config.LOGS, exist_ok=True)
    path = os.path.join(config.LOGS, name)
    return logging.FileHandler(path)
