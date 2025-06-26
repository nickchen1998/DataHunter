from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    """
    用戶個人資料編輯表單
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'username': '使用者名稱',
            'email': 'Email',
            'first_name': '名',
            'last_name': '姓',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '請輸入使用者名稱'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '請輸入 Email'
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
    
    def clean_email(self):
        """
        驗證 email 是否已被其他用戶使用
        """
        email = self.cleaned_data.get('email')
        if email:
            # 檢查是否有其他用戶使用相同的 email（排除當前用戶）
            existing_user = User.objects.filter(email=email).exclude(pk=self.instance.pk).first()
            if existing_user:
                raise forms.ValidationError('此 Email 已被其他用戶使用')
        return email


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