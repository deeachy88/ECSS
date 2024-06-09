import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class IdConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        async_to_sync(self.channel_layer.group_add)(
            'id_number_group',
            self.channel_name
        )
        self.send(text_data=json.dumps({
            'type': 'connection-established',
            'message': 'You are now connected'
        }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'id_number_group',
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        id_number = data['id_number']
        # Save id_number or perform any other server-side logic
        self.send(text_data=json.dumps({
            'message': f"ID number {id_number} received and processed."
        }))

    def send_id_number(self, event):
        id_number = event['id_number']
        self.send(text_data=json.dumps({
            'id_number': event.get('id_number'),
            'full_name': event.get('full_name'),
            'dzongkhag': event.get('dzongkhag'),
            'gewog': event.get('gewog'),
            'village': event.get('village')
        }))
