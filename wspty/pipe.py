import eventlet
import eventlet.event

class GreenletAll:
    def __init__(self, fns):
        self._running_count = len(fns)
        self._event = eventlet.event.Event()
        self._tasks = [eventlet.spawn(self._wrap, fn) for fn in fns]
        self._event.wait()

    def _resolve(self, value=None):
        if not self._event.ready():
            self._event.send(value)

    def _reject(self, reason):
        if not self._event.ready():
            self._event.send_exception(reason)

    def _wrap(self, fn):
        try:
            fn()
            self._running_count -= 1
            if self._running_count <= 0:
                self._resolve()
        except BaseException as e:
            self._reject(e)

    def kill_all(self):
        for g in self._tasks:
            g.kill()


class TerminalPipe:
    def __init__(self, websocket, terminal):
        self.websocket = websocket
        self.terminal = terminal
        self._tasks = None

    def pipe(self):
        try:
            self._tasks = GreenletAll([
                self._pty_to_ws,
                self._ws_to_pty
            ])
        finally:
            self.close()

    def _pty_to_ws(self):
        while True:
            data = self.terminal.read()
            self.websocket.send(data)

    def _ws_to_pty(self):
        while True:
            msg = self.websocket.receive()
            if msg.resize is not None:
                self.terminal.resize(*msg.resize)
            if msg.data is not None:
                self.terminal.write(msg.data)

    def close(self):
        if self._tasks is not None:
            self._tasks.kill_all()


def pipe(websocket, terminal):
    TerminalPipe(websocket, terminal).pipe()
