class BaseTerminal:
    def __init__(self):
        pass

    def send(self, bytes):
        raise NotImplementedError('send')

    def resize(self, cols, rows):
        pass

    def recv(self, count=None):
        raise NotImplementedError('recv')

    def close(self):
        pass
