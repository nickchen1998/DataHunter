from profiles.models import Limit, Profile
from conversations.models import Message


class UserPlanContextMixin:
    """
    提供用戶方案相關的 context 資料的 Mixin
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 只有登入用戶才提供方案資訊
        if self.request.user.is_authenticated:
            user = self.request.user
            
            # 獲取用戶的方案資訊
            limit, created = Limit.objects.get_or_create(user=user)
            profile, created = Profile.objects.get_or_create(user=user)
            
            # 計算今日聊天次數
            today_chat_count = Message.get_today_chat_amount(user)
            
            # 檢查是否為無限制用戶（superuser 或 collaborator）
            is_unlimited = user.is_superuser or profile.is_collaborator
            
            # 檢查是否超過聊天限制
            is_over_chat_limit = not is_unlimited and today_chat_count >= limit.chat_limit_per_day
            
            context.update({
                'user_limit': limit,
                'user_profile': profile,
                'today_chat_count': today_chat_count,
                'is_unlimited': is_unlimited,
                'is_over_chat_limit': is_over_chat_limit,
            })
        else:
            # 未登入用戶的預設值
            context.update({
                'user_limit': None,
                'user_profile': None,
                'today_chat_count': 0,
                'is_unlimited': False,
                'is_over_chat_limit': False,
            })
        
        return context 