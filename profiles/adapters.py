from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.contrib import messages


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
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        處理認證錯誤
        """
        messages.error(
            request,
            f'❌ {provider_id.capitalize()} 登入失敗，請稍後再試。'
        )
        return super().authentication_error(request, provider_id, error, exception, extra_context) 