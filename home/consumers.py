import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from celery_app.tasks.conversations import process_conversation_async
from conversations.models import SenderChoices


class ChatConsumer(AsyncWebsocketConsumer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_message_id = 0
        self.polling = False
        self.message_cache = {}
    
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        
        self.user = self.scope["user"]
        await self.accept()
        
        await self.load_existing_messages()
        
        self.polling = True
        asyncio.create_task(self.poll_messages())

    async def disconnect(self, close_code):
        self.polling = False

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_user_message(data)
            elif message_type == 'clear_conversation':
                await self.handle_clear_conversation()
                
        except Exception as e:
            await self.send_error(f'處理訊息錯誤：{str(e)}')

    async def handle_user_message(self, data):
        user_message = data.get('message', '').strip()
        reference_id_list = data.get('reference_id_list', [])
        data_type = data.get('data_type', 'Mixed')
        
        if not user_message:
            await self.send_error('訊息內容不能為空')
            return
        
        user_message_id, ai_message_id = await self.create_conversation_messages(user_message)
        
        process_conversation_async.delay(
            user_id=self.user.id,
            user_question=user_message,
            reference_id_list=reference_id_list,
            data_type=data_type,
            user_message_id=user_message_id,
            ai_message_id=ai_message_id
        )

    @sync_to_async
    def create_conversation_messages(self, user_message):
        from conversations.models import Session, Message
        
        session = Session.get_or_create_user_session(self.user)
        
        user_msg = Message.create_user_message(session, self.user, user_message)
        ai_msg = Message.create_ai_message(session, self.user, "正在思考中...")
        
        return user_msg.id, ai_msg.id

    async def handle_clear_conversation(self):
        try:
            deleted_count = await self.clear_conversation_messages()
            
            self.last_message_id = 0
            
            await self.send(text_data=json.dumps({
                'type': 'conversation_cleared',
                'message': f'已清空 {deleted_count} 筆對話記錄',
                'deleted_count': deleted_count,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }))
            
        except Exception as e:
            await self.send_error(f'清空對話失敗：{str(e)}')

    @sync_to_async
    def clear_conversation_messages(self):
        from conversations.models import Session, Message
        
        try:
            session = Session.objects.filter(user=self.user).first()
            if not session:
                return 0
            
            deleted_count = Message.clear_conversation(session)
            return deleted_count
            
        except Exception:
            return 0

    async def load_existing_messages(self):
        messages = await self.get_all_messages()
        for message in messages:
            await self.send_message(message)
            self.last_message_id = max(self.last_message_id, message['id'])
            self.message_cache[message['id']] = message.get('text', '')

    async def poll_messages(self):
        while self.polling:
            try:
                new_messages = await self.get_new_messages()
                updated_messages = await self.get_updated_messages()
                
                for message in new_messages:
                    await self.send_message(message)
                    self.last_message_id = max(self.last_message_id, message['id'])
                
                for message in updated_messages:
                    await self.send_message(message)
                
                await asyncio.sleep(1)
                
            except Exception:
                await asyncio.sleep(2)

    @sync_to_async
    def get_all_messages(self):
        from conversations.models import Session, Message
        
        try:
            session = Session.objects.filter(user=self.user).first()
            if not session:
                return []
            
            messages = Message.objects.filter(
                session=session,
                is_deleted=False
            ).exclude(sender=SenderChoices.TOOL).order_by('updated_at')
            
            return [self._format_message(msg) for msg in messages]
            
        except Exception:
            return []

    @sync_to_async
    def get_new_messages(self):
        from conversations.models import Session, Message
        
        try:
            session = Session.objects.filter(user=self.user).first()
            if not session:
                return []
            
            messages = Message.objects.filter(
                session=session,
                is_deleted=False,
                id__gt=self.last_message_id
            ).exclude(sender=SenderChoices.TOOL).order_by('updated_at')[:10]
            
            return [self._format_message(msg) for msg in messages]
            
        except Exception:
            return []

    @sync_to_async
    def get_updated_messages(self):
        from conversations.models import Session, Message
        
        try:
            session = Session.objects.filter(user=self.user).first()
            if not session:
                return []
            
            messages = Message.objects.filter(
                session=session,
                is_deleted=False,
                id__lte=self.last_message_id
            ).exclude(sender=SenderChoices.TOOL).order_by('updated_at')
            
            updated_messages = []
            for msg in messages:
                current_text = msg.text or ''
                cached_text = self.message_cache.get(msg.id, '')
                
                if current_text != cached_text:
                    self.message_cache[msg.id] = current_text
                    updated_messages.append(self._format_message(msg))
            
            return updated_messages
            
        except Exception as e:
            return []

    def _format_message(self, msg):
        message_data = {
            'id': msg.id,
            'type': f"{msg.sender}_message",
            'sender': msg.sender,
            'text': msg.text or '',
            'message': msg.text or '',
            'timestamp': msg.updated_at.strftime('%H:%M:%S'),
            'updated_at_timestamp': msg.updated_at.timestamp()
        }
        
        if msg.sender == 'tool':
            message_data['tool_name'] = msg.tool_name
            message_data['tool_keywords'] = msg.tool_keywords
        
        return message_data

    async def send_message(self, message_data):
        await self.send(text_data=json.dumps(message_data))

    async def send_error(self, error_message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }))