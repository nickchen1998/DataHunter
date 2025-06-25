from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Message, SenderChoices
import json


@login_required
def get_message_tool_calls(request, message_id):
    """獲取指定 AI 訊息的相關工具調用"""
    if request.method != 'GET':
        return JsonResponse({'error': '僅支援 GET 請求'}, status=405)
    
    try:
        # 獲取 AI 訊息
        ai_message = get_object_or_404(
            Message, 
            id=message_id, 
            sender=SenderChoices.AI, 
            user=request.user,
            is_deleted=False
        )
        
        # 獲取相關的工具調用
        tool_messages = ai_message.get_related_tool_messages().order_by('created_at')
        
        # 格式化工具調用資訊
        tool_calls = []
        for tool_msg in tool_messages:
            tool_calls.append({
                'id': tool_msg.id,
                'tool_name': tool_msg.tool_name,
                'tool_keywords': tool_msg.tool_keywords,
                'text': tool_msg.text,
                'timestamp': tool_msg.created_at.strftime('%H:%M:%S'),
                'created_at': tool_msg.created_at.isoformat()
            })
        
        return JsonResponse(tool_calls, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
