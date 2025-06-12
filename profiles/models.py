from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework_api_key.models import AbstractAPIKey


class UserAPIKey(AbstractAPIKey):
    """
    使用者 API Key 模型
    繼承自 AbstractAPIKey，提供安全的 API key 管理
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='api_keys',
        verbose_name='使用者'
    )
    
    name = models.CharField(
        max_length=100, 
        help_text="API Key 的名稱，方便識別用途",
        verbose_name='Key 名稱'
    )
    
    last_used_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="最後一次使用此 API Key 的時間",
        verbose_name='最後使用時間'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='建立時間'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新時間'
    )

    class Meta(AbstractAPIKey.Meta):
        verbose_name = "使用者 API Key"
        verbose_name_plural = "使用者 API Keys"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @property
    def is_expired(self):
        """檢查 API Key 是否已過期"""
        if not self.expiry_date:
            return False
        return timezone.now() > self.expiry_date

    @property
    def is_valid(self):
        """檢查 API Key 是否有效（未過期且未撤銷）"""
        return not self.revoked and not self.is_expired
    
    @property
    def is_active(self):
        """為了向後兼容，映射到 revoked 的反向"""
        return not self.revoked

    def update_last_used(self):
        """更新最後使用時間"""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])

    @classmethod
    def get_valid_keys_for_user(cls, user):
        """取得使用者所有有效的 API Keys"""
        return cls.objects.filter(
            user=user,
            revoked=False
        ).exclude(
            expiry_date__lt=timezone.now()
        )
