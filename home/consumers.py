import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 檢查用戶是否已登入
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        
        self.user = self.scope["user"]
        self.room_group_name = f'chat_{self.user.id}'
        
        # 加入房間群組
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # 離開房間群組
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '').strip()
            
            if not message:
                return
            
            # 回傳用戶訊息確認
            await self.send(text_data=json.dumps({
                'type': 'user_message',
                'message': message,
                'timestamp': self.get_current_timestamp()
            }))
            
            # 模擬思考時間
            await asyncio.sleep(1)
            
            # 發送 AI 回覆（目前固定回覆）
            ai_response = "功能測試中"
            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'message': ai_response,
                'timestamp': self.get_current_timestamp()
            }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '訊息格式錯誤',
                'timestamp': self.get_current_timestamp()
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '處理訊息時發生錯誤',
                'timestamp': self.get_current_timestamp()
            }))

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime('%H:%M:%S') 