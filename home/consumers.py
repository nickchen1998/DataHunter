import json
from typing import Dict, Any, List
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

# 導入聊天代理
from home.agents import ChatAgent


class ChatConsumer(AsyncWebsocketConsumer):
    """統一的聊天 WebSocket 消費者，支援一般聊天和症狀查詢"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_agent = ChatAgent()
    
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        
        self.user = self.scope["user"]
        self.user_id = str(self.user.id)
        self.room_group_name = f'chat_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            result = await self.process_query_with_agent(
                text_data_json.get('message', '').strip(), 
                text_data_json.get('references', []),
                text_data_json.get('data_type', 'Mixed')  # 添加data_type參數，預設為Mixed
            )
            
            # 發送 AI 回覆
            await self.send(text_data=json.dumps({
                'type': 'ai_message',
                'message': result,
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
                'message': f'處理訊息時發生錯誤：{str(e)}',
                'timestamp': self.get_current_timestamp()
            }))

    @sync_to_async
    def process_query_with_agent(self, user_message: str, references: List[Dict[str, Any]], data_type: str = "Mixed") -> str:
        """使用聊天代理處理查詢"""
        try:
            # 調用聊天代理，直接使用前台傳入的data_type
            result = self.chat_agent.process_query(user_message, references, data_type)
            return result
            
        except Exception as e:
            return f"處理查詢時發生錯誤：{str(e)}"

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime('%H:%M:%S') 