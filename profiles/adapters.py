from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
import re
import uuid
from django.http import HttpResponseRedirect

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_connect_redirect_url(self, request, socialaccount):
        """
        當用戶連結社交帳戶後的重定向 URL
        """
        # 添加成功訊息
        provider_name = socialaccount.provider.capitalize()
        messages.success(
            request, 
            f'🎉 {provider_name} 帳戶已成功連結！您現在可以使用 {provider_name} 快速登入。'
        )
        return reverse('profile')
    
    def get_login_redirect_url(self, request):
        """
        社交登入後的重定向 URL
        """
        # 如果是連結操作，跳轉到個人資料頁面
        if 'process' in request.GET and request.GET['process'] == 'connect':
            return reverse('profile')
        # 一般登入跳轉到首頁
        return '/'
    
    def add_message(self, request, level, message_tag, message, **kwargs):
        """
        覆蓋訊息添加方法，禁用登入成功訊息
        """
        # 檢查各種可能的登入成功訊息標籤
        login_message_tags = [
            'account_logged_in',
            'socialaccount_logged_in', 
            'logged_in',
            'login_success'
        ]
        
        # 如果是登入成功相關訊息，直接忽略
        if message_tag in login_message_tags:
            return
            
        # 也可以檢查訊息內容是否包含登入成功的關鍵字
        if message and isinstance(message, str):
            login_keywords = ['登入成功', 'logged in', 'successfully signed in', 'nickchen']
            if any(keyword.lower() in message.lower() for keyword in login_keywords):
                return
        
        # 其他訊息正常處理
        super().add_message(request, level, message_tag, message, **kwargs)
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        處理認證錯誤
        """
        error_message = f'⚠️ {provider_id.capitalize()} 登入失敗'
        if error:
            error_message += f'：{error}'
        messages.error(request, error_message)
        
        # 返回到登入頁面
        return HttpResponseRedirect(reverse('account_login'))
    
    def generate_unique_username(self, txts):
        """
        生成適合檔案系統的唯一 username
        """
        # 從提供的文字中生成基礎 username
        base_username = ""
        for txt in txts:
            if txt:
                # 只保留字母數字和底線，移除其他特殊字符
                clean_txt = re.sub(r'[^a-zA-Z0-9_]', '', str(txt))
                if clean_txt:
                    base_username = clean_txt.lower()
                    break
        
        # 如果沒有有效的文字，使用 user 加上隨機字符
        if not base_username:
            base_username = f"user{uuid.uuid4().hex[:8]}"
        
        # 確保 username 長度合理（最大 30 字符，為數字後綴留空間）
        if len(base_username) > 25:
            base_username = base_username[:25]
        
        # 檢查唯一性，如果重複則添加數字後綴
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            # 防止無限循環
            if counter > 9999:
                username = f"user{uuid.uuid4().hex[:8]}"
                break
        
        return username
    
    def populate_username(self, request, user):
        """
        為社交登入用戶生成 username
        """
        # 從社交帳號資料中提取可能的 username 來源
        sociallogin = request.session.get('socialaccount_sociallogin')
        if sociallogin:
            account_data = sociallogin.get('account', {}).get('extra_data', {})
            email = account_data.get('email', '')
            name = account_data.get('name', '')
            given_name = account_data.get('given_name', '')
            family_name = account_data.get('family_name', '')
            
            # 嘗試不同的 username 來源
            username_candidates = []
            
            # 1. 嘗試使用 given_name
            if given_name:
                username_candidates.append(given_name)
            
            # 2. 嘗試使用 email 的本地部分
            if email:
                local_part = email.split('@')[0]
                username_candidates.append(local_part)
            
            # 3. 嘗試使用完整姓名
            if name:
                username_candidates.append(name.replace(' ', ''))
            
            # 4. 組合姓名
            if given_name and family_name:
                username_candidates.append(f"{given_name}{family_name}")
            
            # 生成唯一的 username
            user.username = self.generate_unique_username(username_candidates)
        
        return super().populate_username(request, user) 