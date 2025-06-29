from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Terms(models.Model):
    """
    使用條款模型
    """
    title = models.CharField(max_length=200, verbose_name="條款標題", default="使用條款")
    content = models.TextField(verbose_name="條款內容（Markdown格式）")
    version = models.CharField(max_length=50, verbose_name="版本號", unique=True)
    is_active = models.BooleanField(default=True, verbose_name="是否為最新版本")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "使用條款"
        verbose_name_plural = "使用條款"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} v{self.version}"

    def save(self, *args, **kwargs):
        """儲存時確保只有一個條款是 active 的"""
        if self.is_active:
            # 將其他條款設為非 active
            Terms.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_latest(cls):
        """取得最新的條款"""
        return cls.objects.filter(is_active=True).first()


class UserTermsAgreement(models.Model):
    """
    使用者條款同意記錄
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="使用者")
    terms = models.ForeignKey(Terms, on_delete=models.CASCADE, verbose_name="條款")
    agreed_at = models.DateTimeField(default=timezone.now, verbose_name="同意時間")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    user_agent = models.TextField(null=True, blank=True, verbose_name="瀏覽器資訊")

    class Meta:
        verbose_name = "使用者條款同意記錄"
        verbose_name_plural = "使用者條款同意記錄"
        unique_together = ['user', 'terms']  # 每個用戶對同一個條款只能同意一次
        ordering = ['-agreed_at']

    def __str__(self):
        return f"{self.user.username} 同意 {self.terms.title} v{self.terms.version}"

    @classmethod
    def has_agreed_to_latest(cls, user):
        """檢查使用者是否已同意最新條款"""
        latest_terms = Terms.get_latest()
        if not latest_terms:
            return True  # 如果沒有條款，則視為已同意
        
        return cls.objects.filter(
            user=user,
            terms=latest_terms
        ).exists()

    @classmethod
    def create_agreement(cls, user, terms, ip_address=None, user_agent=None):
        """建立同意記錄"""
        agreement, created = cls.objects.get_or_create(
            user=user,
            terms=terms,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent,
            }
        )
        return agreement, created
