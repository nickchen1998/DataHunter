from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from .forms import EmailAuthenticationForm

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
