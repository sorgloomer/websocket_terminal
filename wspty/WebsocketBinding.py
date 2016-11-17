import json


class DataPacket:
    def __init__(self, msg):
        self.data = msg.get('data')
        resize = msg.get('resize')
        self.resize = None if resize is None else (resize.get('width', 80), resize.get('height', 24))


class WebsocketBinding:
    def __init__(self, ws):
        self.websocket = ws

    def send(self, data_str):
        self.websocket.send(json.dumps({'data': data_str}))

    def send_error(self, error_str):
        self.websocket.send(json.dumps({'error': str(error_str)}))

    def receive(self):
        return DataPacket(json.loads(self.websocket.wait()))
