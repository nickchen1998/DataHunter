from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib.auth import logout, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import EmailAuthenticationForm, UserProfileForm, CustomPasswordChangeForm

@method_decorator(never_cache, name='dispatch')
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'
    login_url = '/login/'  # 未登入時重定向的 URL

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        return context

class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = EmailAuthenticationForm  # 使用自定義表單
    success_url = reverse_lazy('home')  # 登入成功後重定向到首頁
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')  # 如果已登入，直接跳轉到首頁
        return super().dispatch(request, *args, **kwargs)

class CustomLogoutView(View):
    """
    自定義登出視圖，確保正確清除會話並重定向到登入頁
    """
    def get(self, request):
        return self.logout_user(request)
    
    def post(self, request):
        return self.logout_user(request)
    
    def logout_user(self, request):
        # 清除會話
        logout(request)
        
        # 創建重定向響應
        response = HttpResponseRedirect('/login/')
        
        # 添加緩存控制標頭，防止瀏覽器緩存
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response

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
        
        context = {
            'profile_form': profile_form,
            'password_form': password_form,
            'user': request.user,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'update_profile':
            return self._handle_profile_update(request)
        elif action == 'change_password':
            return self._handle_password_change(request)
        
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
