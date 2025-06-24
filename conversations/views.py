from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import Session, Message, SenderChoices
import json

# Create your views here.

@login_required
@require_http_methods(["GET"])
def get_conversation_history(request):
    """獲取使用者的對話歷史記錄"""
    try:
        # 取得使用者的 session
        session = Session.objects.filter(user=request.user).first()
        
        if not session:
            return JsonResponse({
                'success': True,
                'messages': []
            })
        
        # 獲取所有訊息，按時間排序
        messages = Message.objects.filter(session=session).order_by('created_at')
        
        # 格式化訊息資料
        message_list = []
        for message in messages:
            message_data = {
                'id': message.id,
                'sender': message.sender,
                'text': message.text or '',
                'created_at': message.created_at.strftime('%H:%M:%S'),
                'timestamp': message.created_at.strftime('%H:%M:%S')  # 兼容前台格式
            }
            
            # 如果是工具訊息，添加額外資訊
            if message.sender == SenderChoices.TOOL:
                message_data['tool_name'] = message.tool_name
                message_data['tool_params'] = message.tool_keywords
            
            message_list.append(message_data)
        
        return JsonResponse({
            'success': True,
            'messages': message_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
