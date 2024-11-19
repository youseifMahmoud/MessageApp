import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from users.models import Thread, ChatMessage

User = get_user_model()

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('connected', event)
        user = self.scope['user']
        thread_id = self.scope['url_route']['kwargs']['thread_id']  # Get thread_id from URL
        self.chat_room = f'thread_{thread_id}'  # Use thread_id for room name

        await self.channel_layer.group_add(
            self.chat_room,
            self.channel_name
        )
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_receive(self, event):
        print('receive', event)
        received_data = json.loads(event['text'])
        msg = received_data.get('message')
        sent_by_id = received_data.get('sent_by')
        send_to_id = received_data.get('send_to')
        thread_id = received_data.get('thread_id')

        if not msg:
            print('Error:: empty message')
            return False

        sent_by_user = await self.get_user_object(sent_by_id)
        send_to_user = await self.get_user_object(send_to_id)
        thread_obj = await self.get_thread(thread_id)
        if not sent_by_user:
            print('Error:: sent by user is incorrect')
        if not send_to_user:
            print('Error:: send to user is incorrect')
        if not thread_obj:
            print('Error:: Thread id is incorrect')

        await self.create_chat_message(thread_obj, sent_by_user, msg)

        # Use self.chat_room defined in websocket_connect
        response = {
            'message': msg,
            'sent_by': sent_by_id,
            'thread_id': thread_id
        }

        # Send message to both users in the chat room
        await self.channel_layer.group_send(
            self.chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )

    async def websocket_disconnect(self, event):
        print('disconnect', event)
        await self.channel_layer.group_discard(
            self.chat_room,
            self.channel_name
        )

    @database_sync_to_async
    def create_chat_message(self, thread, user, msg):
        return ChatMessage.objects.create(thread=thread, user=user, message=msg)  # Ensure this is correct

    @database_sync_to_async
    def get_user_object(self, user_id):
        qs = User.objects.filter(id=user_id)
        return qs.first() if qs.exists() else None

    @database_sync_to_async
    def get_thread(self, thread_id):
        qs = Thread.objects.filter(id=thread_id)
        return qs.first() if qs.exists() else None
