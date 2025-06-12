from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .forms import UserProfileForm, CustomPasswordChangeForm
from .models import UserAPIKey


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


@method_decorator(never_cache, name='dispatch')
class UserAPIKeyListView(LoginRequiredMixin, View):
    """
    API Key 列表視圖 - 處理 AJAX 請求
    """
    login_url = '/login/'
    MAX_KEYS_PER_USER = 5
    
    def get(self, request):
        """取得使用者的 API Keys 列表（只顯示未撤銷的）"""
        api_keys = request.user.api_keys.filter(revoked=False).order_by('-created_at')
        
        keys_data = []
        for key in api_keys:
            keys_data.append({
                'id': key.id,
                'name': key.name,
                'prefix': key.prefix,
                'created_at': key.created_at.strftime('%Y年%m月%d日'),
                'expires_at': key.expiry_date.strftime('%Y年%m月%d日') if key.expiry_date else None,
                'last_used_at': key.last_used_at.strftime('%Y年%m月%d日') if key.last_used_at else '從未使用',
                'is_active': key.is_active,  # 這是我們的 property，映射到 not revoked
                'is_expired': key.is_expired,
                'is_valid': key.is_valid,
                # 注意：不再包含完整的 key 數據，只在創建時提供
            })
        
        return JsonResponse({
            'success': True,
            'keys': keys_data,
            'total_keys': len(keys_data),
            'max_keys': self.MAX_KEYS_PER_USER,
            'can_create_more': len(keys_data) < self.MAX_KEYS_PER_USER
        })
    
    def post(self, request):
        """建立新的 API Key"""
        # 檢查是否已達到最大數量限制
        current_keys_count = request.user.api_keys.filter(revoked=False).count()
        if current_keys_count >= self.MAX_KEYS_PER_USER:
            return JsonResponse({
                'success': False,
                'error': f'每個使用者最多只能擁有 {self.MAX_KEYS_PER_USER} 個啟用中的 API Key'
            })
        
        name = request.POST.get('name', '').strip()
        expires_period = request.POST.get('expires_period', '').strip()
        
        # 驗證輸入
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'API Key 名稱不能為空'
            })
        
        if len(name) > 100:
            return JsonResponse({
                'success': False,
                'error': 'API Key 名稱不能超過 100 個字元'
            })
        
        # 檢查名稱是否重複
        if request.user.api_keys.filter(name=name, revoked=False).exists():
            return JsonResponse({
                'success': False,
                'error': '該名稱的 API Key 已存在'
            })
        
        # 處理到期時間
        expires_at = None
        if expires_period and expires_period != 'never':
            period_mapping = {
                '1month': 30,
                '3months': 90,
                '6months': 180,
                '1year': 365,
            }
            
            if expires_period in period_mapping:
                days = period_mapping[expires_period]
                expires_at = timezone.now() + timedelta(days=days)
            else:
                return JsonResponse({
                    'success': False,
                    'error': '無效的到期時間選項'
                })
        
        try:
            # 建立 API Key
            api_key, key = UserAPIKey.objects.create_key(
                user=request.user,
                name=name,
                expiry_date=expires_at
            )
            
            return JsonResponse({
                'success': True,
                'message': 'API Key 建立成功！',
                'key_data': {
                    'id': api_key.id,
                    'name': api_key.name,
                    'key': key,  # 只在建立時返回完整的 key
                    'prefix': api_key.prefix,
                    'created_at': api_key.created_at.strftime('%Y年%m月%d日'),
                    'expires_at': api_key.expiry_date.strftime('%Y年%m月%d日') if api_key.expiry_date else None,
                    'last_used_at': '從未使用',
                    'is_active': api_key.is_active,  # property 映射到 not revoked
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'建立 API Key 時發生錯誤：{str(e)}'
            })


@method_decorator(never_cache, name='dispatch')
class UserAPIKeyDetailView(LoginRequiredMixin, View):
    """
    API Key 詳細視圖 - 處理個別 API Key 的操作
    """
    login_url = '/login/'
    
    def get_object(self, request, prefix):
        """取得使用者的指定 API Key"""
        return get_object_or_404(
            UserAPIKey, 
            prefix=prefix, 
            user=request.user
        )
    
    def patch(self, request, prefix):
        """更新 API Key"""
        api_key = self.get_object(request, prefix)
        
        # 解析 PATCH 資料
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '無效的 JSON 資料'
            })
        
        field = data.get('field')
        value = data.get('value')
        
        if field == 'name':
            if not value or not value.strip():
                return JsonResponse({
                    'success': False,
                    'error': 'API Key 名稱不能為空'
                })
            
            if len(value.strip()) > 100:
                return JsonResponse({
                    'success': False,
                    'error': 'API Key 名稱不能超過 100 個字元'
                })
            
            # 檢查名稱是否重複（排除自己）
            if request.user.api_keys.filter(
                name=value.strip(), 
                revoked=False
            ).exclude(id=api_key.id).exists():
                return JsonResponse({
                    'success': False,
                    'error': '該名稱的 API Key 已存在'
                })
            
            api_key.name = value.strip()
            
        elif field == 'expires_at':
            if value == 'never':
                api_key.expiry_date = None
            else:
                # 處理預設時間週期
                period_mapping = {
                    '1month': 30,
                    '3months': 90,
                    '6months': 180,
                    '1year': 365,
                }
                
                if value in period_mapping:
                    days = period_mapping[value]
                    api_key.expiry_date = timezone.now() + timedelta(days=days)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': '無效的到期時間選項'
                    })
        else:
            return JsonResponse({
                'success': False,
                'error': '不支援的欄位更新'
            })
        
        try:
            api_key.save()
            
            # 處理返回的更新值
            updated_value = value
            if field == 'expires_at':
                if api_key.expiry_date:
                    updated_value = api_key.expiry_date.strftime('%Y年%m月%d日')
                else:
                    updated_value = '永不過期'
            
            return JsonResponse({
                'success': True,
                'message': '更新成功',
                'updated_value': updated_value
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'更新時發生錯誤：{str(e)}'
            })
    
    def delete(self, request, prefix):
        """刪除（停用）API Key"""
        api_key = self.get_object(request, prefix)
        
        try:
            api_key.revoked = True
            api_key.save()
            
            return JsonResponse({
                'success': True,
                'message': 'API Key 已成功刪除'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'刪除時發生錯誤：{str(e)}'
            })
