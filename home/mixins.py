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
            
            # 計算私有資料源數量
            from sources.models import Source
            private_source_count = Source.objects.filter(
                user=user
            ).count()
            
            # 檢查用戶權限層級
            is_superuser = user.is_superuser
            is_collaborator = profile.is_collaborator
            
            # 各項功能的限制狀態
            has_unlimited_chat = is_superuser or is_collaborator  # 超級使用者和協作者都有無限對話
            has_unlimited_source = is_superuser  # 只有超級使用者有無限資料源
            has_unlimited_files = is_superuser  # 只有超級使用者有無限檔案
            
            # 檢查是否超過聊天限制
            is_over_chat_limit = not has_unlimited_chat and today_chat_count >= limit.chat_limit_per_day
            
            context.update({
                'user_limit': limit,
                'user_profile': profile,
                'today_chat_count': today_chat_count,
                'private_source_count': private_source_count,
                'is_unlimited': has_unlimited_chat,  # 為了向後相容，保留這個變數名
                'has_unlimited_chat': has_unlimited_chat,
                'has_unlimited_source': has_unlimited_source,
                'has_unlimited_files': has_unlimited_files,
                'is_over_chat_limit': is_over_chat_limit,
            })
        else:
            # 未登入用戶的預設值
            context.update({
                'user_limit': None,
                'user_profile': None,
                'today_chat_count': 0,
                'private_source_count': 0,
                'is_unlimited': False,
                'has_unlimited_chat': False,
                'has_unlimited_source': False,
                'has_unlimited_files': False,
                'is_over_chat_limit': False,
            })
        
        return context 