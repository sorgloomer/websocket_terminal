import subprocess
import os

import eventlet.queue
import eventlet.tpool
import eventlet.green.subprocess
from eventlet import green
from eventlet.greenpool import GreenPool

from .BaseTerminal import BaseTerminal

import logging
logger = logging.getLogger(__name__)

OS_TERMINALS = {
    'posix': ['bash'],
    'nt': ['cmd']
}


class SubprocessTerminal(BaseTerminal):
    def __init__(self, cmd):
        self.process = make_simple_process(cmd)
        self.queue = eventlet.queue.Queue()
        self.echo = True
        self.greenpool = self._start_consume()

    def _start_consume(self):
        greenpool = GreenPool(5)
        greenpool.spawn_n(self._consume_stream, self.process.stdout)
        greenpool.spawn_n(self._consume_stream, self.process.stderr)
        return greenpool

    def _consume_stream(self, stream):
        while True:
            data = stream.read()
            if not data:
                break
            self.queue.put(data)

    def recv(self, count=None):
        return self.queue.get()

    def send(self, data):
        data = terminal_encode(data)
        if self.echo:
            self.queue.put(data)
        self.process.stdin.write(data)

    def close(self):
        self.process.kill()


class NonBlockingSimplePipe:
    def __init__(self, stream):
        logger.debug("NonBlockingSimplePipe.__init__ type(stream) == {}".format(type(stream)))
        logger.debug("NonBlockingSimplePipe.__init__ type(stream).__name__ == {!r}".format(type(stream).__name__))
        self.needs_thread = not is_greenpipe(stream)
        self.stream = stream

    def read(self):
        if self.needs_thread:
            return eventlet.tpool.execute(self._read)
        return self._read()

    def write(self, data):
        if self.needs_thread:
            return eventlet.tpool.execute(self._write, data)
        return self._write(data)

    def _read(self):
        return self.stream.read(2048)

    def _write(self, data):
        self.stream.write(data)
        self.stream.flush()


class NonBlockingSimpleProcess:
    def __init__(self, cmd):
        self.proc = make_subprocess(cmd)
        self.stdin = NonBlockingSimplePipe(self.proc.stdin)
        self.stdout = NonBlockingSimplePipe(self.proc.stdout)
        self.stderr = NonBlockingSimplePipe(self.proc.stderr)

    def kill(self):
        self.proc.kill()


def is_greenpipe(obj):
    # GreenFileIO is not exposed and GreenPipe is not a class, so checking by name
    return type(obj).__name__ == "GreenFileIO"


def os_terminal():
    return SubprocessTerminal(OS_TERMINALS[os.name])


def terminal_encode(binary: bytes):
    return binary.replace(b'\r', b'\r\n')


def make_subprocess(obj):
    def green_popen(cmd):
        p = subprocess.PIPE
        return green.subprocess.Popen(cmd, stdin=p, stdout=p, stderr=p, bufsize=0)
    if isinstance(obj, str):
        return green_popen([obj])
    if isinstance(obj, list):
        return green_popen(obj)
    if isinstance(obj, subprocess.Popen):
        return obj
    if isinstance(obj, green.subprocess.Popen):
        return obj
    raise Exception("Invalid argument to make_subprocess: {}".format(type(obj)))


def make_simple_process(obj):
    if isinstance(obj, NonBlockingSimpleProcess):
        return obj
    proc = make_subprocess(obj)
    return NonBlockingSimpleProcess(proc)
