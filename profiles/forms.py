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