from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailAuthenticationForm(AuthenticationForm):
    """
    自定義登入表單，允許用戶使用 email 登入
    """
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full pl-10',
            'placeholder': '請輸入您的 Email'
        })
    )
    
    password = forms.CharField(
        label='密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full pl-10',
            'placeholder': '請輸入密碼'
        })
    )
    
    def clean_username(self):
        email = self.cleaned_data.get('username')
        if email:
            # 嘗試通過 email 找到對應的 username
            try:
                user = User.objects.get(email=email)
                return user.username  # 返回實際的 username 供認證使用
            except User.DoesNotExist:
                raise forms.ValidationError('找不到使用此 Email 的用戶')
        return email

class UserProfileForm(forms.ModelForm):
    """
    用戶個人資料編輯表單
    """
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        labels = {
            'username': '使用者名稱',
            'first_name': '名',
            'last_name': '姓',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '請輸入使用者名稱'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '請輸入名'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '請輸入姓'
            }),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    自定義密碼修改表單
    """
    old_password = forms.CharField(
        label='當前密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請輸入當前密碼'
        })
    )
    new_password1 = forms.CharField(
        label='新密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請輸入新密碼'
        })
    )
    new_password2 = forms.CharField(
        label='確認新密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '請再次輸入新密碼'
        })
    ) 