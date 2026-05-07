import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class IdConsumer(WebsocketConsumer):

    def connect(self):

        self.thread_id = self.scope['url_route']['kwargs']['thread_id']

        self.group_name = f"ndi_{self.thread_id}"

        self.accept()

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected successfully',
            'thread_id': self.thread_id
        }))

    def disconnect(self, close_code):

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):

        data = json.loads(text_data)

        self.send(text_data=json.dumps({
            'message': 'Message received successfully'
        }))

    def send_id_number(self, event):

        self.send(text_data=json.dumps({
            'id_number': event.get('id_number'),
            'full_name': event.get('full_name'),
            'dzongkhag': event.get('dzongkhag'),
            'gewog': event.get('gewog'),
            'village': event.get('village'),
            'thid': event.get('thid'),
            'relationshipDid': event.get('relationshipDid'),
            'holder_did': event.get('holder_did'),
            'category': event.get('category'),
            'eid': event.get('eid'),
            'session_id': event.get('session_id'),
            'proof_type': event.get('proof_type')
        }))