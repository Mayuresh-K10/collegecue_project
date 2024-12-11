import json
from channels.generic.websocket import AsyncWebsocketConsumer
import re

class ChatConsumer(AsyncWebsocketConsumer):
    def sanitize_group_name(self, group_name):
        """
        Sanitize the group name to comply with Django Channels requirements.
        Replace invalid characters with valid ones.
        """
        return re.sub(r'[^a-zA-Z0-9_.-]', '_', group_name)[:100]  # Ensure < 100 chars

    async def connect(self):
        """
        Accept connection and determine group based on sender/recipient emails.
        """
        self.sender_email = self.scope["query_string"].decode("utf-8").split("&")[0].split("=")[1]
        self.sender_model = self.scope["query_string"].decode("utf-8").split("&")[1].split("=")[1]
        self.sender_token = self.scope["query_string"].decode("utf-8").split("&")[2].split("=")[1]

        raw_group_name = f"chat_{self.sender_email}_{self.sender_model}"
        self.room_group_name = self.sanitize_group_name(raw_group_name)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """
        Leave the group on disconnect.
        """
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            print(f"Error during disconnect: {str(e)}")

    async def receive(self, text_data):
        """
        Handle incoming messages with support for attachments and subjects.
        """
        data = json.loads(text_data)

        sender_email = data["sender_email"]
        recipient_email = data["recipient_email"]
        sender_model = data["sender_model"]
        recipient_model = data["recipient_model"]
        content = data.get("content", "").strip()
        subject = data.get("subject", "").strip()
        attachments = data.get("attachments", [])  # Base64-encoded file data

        try:
            # Sanitize recipient group name
            recipient_group_name = self.sanitize_group_name(f"chat_{recipient_email}_{recipient_model}")

            # Broadcast the message
            await self.channel_layer.group_send(
                recipient_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "sender_email": sender_email,
                        "recipient_email": recipient_email,
                        "sender_model": sender_model,
                        "recipient_model": recipient_model,
                        "subject": subject,
                        "content": content,
                        "attachments": attachments,
                    },
                }
            )

        except Exception as e:
            print(f"Error handling message: {str(e)}")

    async def chat_message(self, event):
        """
        Send the broadcast message to the WebSocket.
        """
        await self.send(text_data=json.dumps(event["message"]))


#import json
#from urllib.parse import parse_qs
#from channels.generic.websocket import AsyncWebsocketConsumer
#from django.contrib.auth.models import AnonymousUser
#from asgiref.sync import sync_to_async
#from django.db.models import Q, Max
#from .models import Message, MessageAttachment, OnlineStatus
#from login.models import JobSeeker, new_user, CompanyInCharge, UniversityInCharge
#from rest_framework.authtoken.models import Token
#from channels.db import database_sync_to_async
#import re
#
#MODEL_MAPPING = {
#    "JobSeeker": JobSeeker,
#    "UniversityInCharge": UniversityInCharge,
#    "CompanyInCharge": CompanyInCharge,
#    "new_user": new_user,
#}
#
#
#
#async def get_user_from_token(token_key):
#    try:
#        token = await database_sync_to_async(Token.objects.get)(key=token_key)
#        return token.user
#    except Token.DoesNotExist:
#        print(f"Token does not exist: {token_key}")
#        return None
#
#class ChatConsumer(AsyncWebsocketConsumer):
#    async def connect(self):
#        # Extract room name from URL path
#        self.room_name = self.scope['url_route']['kwargs']['room_name']
#
#        # Sanitize the room name by removing invalid characters
#        sanitized_room_name = re.sub(r'[^a-zA-Z0-9-_\.]', '_', self.room_name)
#
#        # Create a valid group name
#        self.room_group_name = f"chat_{sanitized_room_name}"
#
#        # Add the user to the group (no user validation or token check)
#        await self.channel_layer.group_add(
#            self.room_group_name,
#            self.channel_name
#        )
#
#        # Accept the WebSocket connection
#        await self.accept()
#
#        # Send a welcome message (optional)
#        await self.send(text_data=json.dumps({
#            'message': f"Welcome to the room: {self.room_name}!"
#        }))
#
#    async def disconnect(self, close_code):
#        # Remove the user from the group when they disconnect
#        if hasattr(self, 'room_group_name'):
#            await self.channel_layer.group_discard(
#                self.room_group_name,
#                self.channel_name
#            )
#
#    async def receive(self, text_data):
#        """Handle incoming WebSocket messages."""
#        try:
#            data = json.loads(text_data)
#            action = data.get("action")
#
#            if action == "send_message":
#                await self.send_message(data)
#            elif action == "get_messages":
#                await self.get_messages(data)
#            elif action == "inbox":
#                await self.inbox(data)
#            elif action == "search_user":
#                await self.search_user(data)
#            else:
#                await self.send_json({"error": "Invalid action"})
#        except Exception as e:
#            await self.send_json({"error": f"Error processing message: {str(e)}"})
#
#    async def send_message(self, data):
#        """Send a chat message."""
#        sender_model = data.get("sender_model")
#        sender_email = data.get("sender_email")
#        recipient_email = data.get("recipient_email")
#        recipient_model = data.get("recipient_model")
#        content = data.get("content", "").strip()
#        subject = data.get("subject", "").strip()
#        attachments = data.get("attachments", [])
#
#        if not all([sender_model, sender_email, recipient_email, recipient_model]):
#            await self.send_json({"error": "Missing required fields"})
#            return
#
#        if sender_model not in MODEL_MAPPING or recipient_model not in MODEL_MAPPING:
#            await self.send_json({"error": "Invalid sender_model or recipient_model"})
#            return
#
#        sender_model_class = MODEL_MAPPING[sender_model]
#        recipient_model_class = MODEL_MAPPING[recipient_model]
#
#        try:
#            # Validate sender and recipient
#            sender = await sync_to_async(sender_model_class.objects.get)(
#                email=sender_email if hasattr(sender_model_class, "email") else {"official_email": sender_email}
#            )
#            recipient = await sync_to_async(recipient_model_class.objects.get)(
#                email=recipient_email if hasattr(recipient_model_class, "email") else {"official_email": recipient_email}
#            )
#
#            # Create the message
#            message = await sync_to_async(Message.objects.create)(
#                sender_email=sender_email,
#                recipient_email=recipient_email,
#                sender_model=sender_model,
#                recipient_model=recipient_model,
#                content=content,
#                subject=subject,
#            )
#
#            # Handle attachments
#            for attachment_data in attachments:
#                file = attachment_data['file']
#                original_name = attachment_data['original_name']
#                file_type = attachment_data['file_type']
#
#                attachment = await sync_to_async(MessageAttachment.objects.create)(
#                    file=file,
#                    original_name=original_name,
#                    file_type=file_type
#                )
#                await sync_to_async(message.attachments.add)(attachment)
#
#            # Notify the room group of the new message
#            await self.channel_layer.group_send(
#                self.room_group_name,
#                {
#                    "type": "chat_message",
#                    "message": {
#                        "id": message.id,
#                        "sender_email": sender_email,
#                        "recipient_email": recipient_email,
#                        "subject": subject,
#                        "content": content,
#                        "attachments": [{"original_name": a.original_name, "file_url": a.file.url} for a in message.attachments.all()],
#                        "timestamp": str(message.timestamp)
#                    }
#                }
#            )
#        except Exception as e:
#            await self.send_json({"error": f"Error sending message: {str(e)}"})
#
#    async def chat_message(self, event):
#        """Send a message to WebSocket clients."""
#        await self.send(text_data=json.dumps(event["message"]))
#
#    async def get_messages(self, data):
#        """Retrieve chat messages between two users."""
#        sender_email = data.get("sender_email")
#        recipient_email = data.get("recipient_email")
#
#        if not all([sender_email, recipient_email]):
#            await self.send_json({"error": "Missing required fields"})
#            return
#
#        try:
#            messages = await sync_to_async(list)(
#                Message.objects.filter(
#                    Q(sender_email=sender_email, recipient_email=recipient_email) |
#                    Q(sender_email=recipient_email, recipient_email=sender_email)
#                ).order_by('timestamp')
#            )
#
#            await self.send_json({
#                "messages": [
#                    {
#                        "id": msg.id,
#                        "sender_email": msg.sender_email,
#                        "recipient_email": msg.recipient_email,
#                        "subject": msg.subject,
#                        "content": msg.content,
#                        "timestamp": str(msg.timestamp),
#                        "attachments": [{"original_name": a.original_name, "file_url": a.file.url} for a in msg.attachments.all()]
#                    }
#                    for msg in messages
#                ]
#            })
#        except Exception as e:
#            await self.send_json({"error": f"Error retrieving messages: {str(e)}"})
#
#    async def inbox(self, data):
#        """Retrieve the user's inbox."""
#        user_email = data.get("user_email")
#
#        if not user_email:
#            await self.send_json({"error": "user_email is required"})
#            return
#
#        try:
#            subquery = Message.objects.filter(
#                Q(sender_email=user_email) | Q(recipient_email=user_email)
#            ).values(
#                'sender_email', 'recipient_email'
#            ).annotate(latest_message_id=Max('id'))
#
#            latest_message_ids = [entry['latest_message_id'] for entry in subquery]
#            messages = await sync_to_async(list)(
#                Message.objects.filter(id__in=latest_message_ids).order_by('-timestamp')
#            )
#
#            inbox_data = []
#            seen_conversations = set()
#
#            for msg in messages:
#                conversation_with = msg.recipient_email if msg.sender_email == user_email else msg.sender_email
#                if conversation_with in seen_conversations:
#                    continue
#
#                seen_conversations.add(conversation_with)
#                inbox_data.append({
#                    "conversation_with": conversation_with,
#                    "subject": msg.subject,
#                    "latest_message": msg.content,
#                    "timestamp": str(msg.timestamp),
#                })
#
#            await self.send_json({"inbox": inbox_data})
#        except Exception as e:
#            await self.send_json({"error": f"Error retrieving inbox: {str(e)}"})
#
#    async def search_user(self, data):
#        """Search for users."""
#        query = data.get("query", "").strip()
#
#        if not query:
#            await self.send_json({"error": "Search query cannot be empty"})
#            return
#
#        results = []
#        try:
#            for model_name, model_class in MODEL_MAPPING.items():
#                queryset = await sync_to_async(list)(
#                    model_class.objects.filter(
#                        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
#                    )
#                )
#
#                results.extend([
#                    {
#                        "id": user.id,
#                        "model": model_name,
#                        "email": user.email,
#                        "name": f"{user.first_name} {user.last_name}"
#                    }
#                    for user in queryset
#                ])
#
#            await self.send_json({"results": results})
#        except Exception as e:
#            await self.send_json({"error": f"Error searching users: {str(e)}"})
#