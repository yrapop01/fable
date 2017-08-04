from functools import partial
import traceback
import logging
import sys
import os
import io
import aiofiles
from datetime import datetime
from fable import config

class Logger:
    def __init__(self, path, level=logging.DEBUG):
        self.path = path
        self.level = level
        self.time_format = '%Y-%m-%d %H:%M:%S'

    def format(self, level, *arg, **kw):
        with io.StringIO() as f:
            print(*arg, **kw, file=f)
            value = f.getvalue()
        level = logging.getLevelName(level)
        time = datetime.now().strftime(self.time_format)

        return ' - '.join([time, level, value])

    async def alog(self, level, *arg, **kw):
        if level >= self.level:
            async with aiofiles.open(self.path, mode='a+') as f:
                await f.write(self.format(level, *arg, **kw))

    async def ainfo(self, *args, **kw):
        await self.alog(logging.INFO, *args, **kw)

    async def adebug(self, *args, **kw):
        await self.alog(logging.DEBUG, *args, **kw)

    async def awarning(self, *args, **kw):
        await self.alog(logging.WARNING, *args, **kw)

    async def acritical(self, *args, **kw):
        await self.alog(logging.CRITICAL, *args, **kw)

    async def aerror(self, *args, **kw):
        await self.alog(logging.ERROR, *args, **kw)

    async def aexception(self):
        with io.StringIO() as f:
            traceback.print_exc(file=f)
            value = f.getvalue()
        async with aiofiles.open(self.path, mode='a+') as f:
            await f.write(value)

    def log(self, level, *args, **kw):
        if level >= self.level:
            with open(self.path, mode='a+') as f:
                f.write(self.format(level, *args, **kw))

    def info(self, *args, **kw):
        self.log(logging.INFO, *args, **kw)

    def debug(self, *args, **kw):
        self.log(logging.DEBUG, *args, **kw)

    def warning(self, *args, **kw):
        self.log(logging.WARNING, *args, **kw)

    def critical(self, *args, **kw):
        self.log(logging.CRITICAL, *args, **kw)

    def error(self, *args, **kw):
        self.log(logging.ERROR, *args, **kw)

    def exception(self):
        with io.StringIO() as f:
            traceback.print_exc(file=f)
            value = f.getvalue()
        with open(self.path, mode='a+') as f:
            f.write(value)

def log(name):
    os.makedirs(config.LOGS, exist_ok=True)
    path = os.path.join(config.LOGS, name)
    log = Logger(path)

    return log

def handler(name):
    os.makedirs(config.LOGS, exist_ok=True)
    path = os.path.join(config.LOGS, name)
    return logging.FileHandler(path)

def shutdown():
    logging.shutdown()
