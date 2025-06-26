from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib.auth import update_session_auth_hash, logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import UserProfileForm, CustomPasswordChangeForm
from .models import Limit, Profile
from conversations.models import Message

# Create your views here.

@method_decorator(never_cache, name='dispatch')
class ProfileView(LoginRequiredMixin, View):
    """
    個人資料管理視圖
    """
    login_url = '/login/'
    template_name = 'profile.html'
    
    def get(self, request):
        profile_form = UserProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)
        
        # 獲取或創建使用者的 Limit 和 Profile 記錄
        limit, created = Limit.objects.get_or_create(user=request.user)
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # 檢查用戶權限層級
        is_superuser = request.user.is_superuser
        is_collaborator = profile.is_collaborator
        
        # 各項功能的限制狀態
        has_unlimited_chat = is_superuser or is_collaborator  # 超級使用者和協作者都有無限對話
        has_unlimited_source = is_superuser  # 只有超級使用者有無限資料源
        has_unlimited_files = is_superuser  # 只有超級使用者有無限檔案
        
        # 計算今日聊天次數（包含已刪除的訊息）
        today_chat_count = Message.get_today_chat_amount(request.user)
        
        # 計算私有資料源數量（這裡假設您有相關模型，如果沒有則設為 0）
        private_source_count = 0  # 待實作：根據您的私有資料源模型計算
        
        # 計算使用百分比
        chat_usage_percentage = 0 if has_unlimited_chat else (
            (today_chat_count / limit.chat_limit_per_day * 100) if limit.chat_limit_per_day > 0 else 0
        )
        source_usage_percentage = 0 if has_unlimited_source else (
            (private_source_count / limit.private_source_limit * 100) if limit.private_source_limit > 0 else 0
        )
        
        context = {
            'profile_form': profile_form,
            'password_form': password_form,
            'user': request.user,
            'user_limit': limit,
            'user_profile': profile,
            'today_chat_count': today_chat_count,
            'private_source_count': private_source_count,
            'chat_usage_percentage': chat_usage_percentage,
            'source_usage_percentage': source_usage_percentage,
            'is_superuser': is_superuser,
            'is_collaborator': is_collaborator,
            'has_unlimited_chat': has_unlimited_chat,
            'has_unlimited_source': has_unlimited_source,
            'has_unlimited_files': has_unlimited_files,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'update_profile':
            return self._handle_profile_update(request)
        elif action == 'change_password':
            return self._handle_password_change(request)
        elif action == 'delete_account':
            return self._handle_account_deletion(request)
        
        return self.get(request)
    
    def _handle_profile_update(self, request):
        """處理個人資料更新"""
        profile_form = UserProfileForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)
        
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, '個人資料已成功更新！')
            return redirect('profile')
        else:
            messages.error(request, '個人資料更新失敗，請檢查輸入的資料。')
        
        context = {
            'profile_form': profile_form,
            'password_form': password_form,
            'user': request.user,
        }
        return render(request, self.template_name, context)
    
    def _handle_password_change(self, request):
        """處理密碼修改"""
        profile_form = UserProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # 重要：更新會話，避免用戶被登出
            messages.success(request, '密碼已成功修改！')
            return redirect('profile')
        else:
            messages.error(request, '密碼修改失敗，請檢查輸入的密碼。')
        
        context = {
            'profile_form': profile_form,
            'password_form': password_form,
            'user': request.user,
        }
        return render(request, self.template_name, context)
    
    def _handle_account_deletion(self, request):
        """處理帳號刪除"""
        confirmation = request.POST.get('confirmation', '').strip()
        
        if confirmation != request.user.username:
            messages.error(request, '確認文字不正確，帳號刪除失敗。')
            return redirect('profile')
        
        # 刪除使用者帳號
        username = request.user.username
        request.user.delete()
        logout(request)
        
        messages.success(request, f'帳號 {username} 已成功刪除。感謝您的使用！')
        return redirect('home')
