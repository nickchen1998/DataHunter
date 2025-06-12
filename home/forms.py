from django import forms
from django.contrib.auth.forms import AuthenticationForm
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