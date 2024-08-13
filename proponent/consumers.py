import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class SimpleConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        async_to_sync(self.channel_layer.group_add)(
            'test_group',
            self.channel_name
        )
        self.send(text_data=json.dumps({
            'type': 'connection-established',
            'message': 'You are now connected'
        }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'test_group',
            self.channel_name
        )

    def receive(self, text_data):
        self.send(text_data=json.dumps({
            'message': 'Message received: ' + text_data
        }))

    def send_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
    }))