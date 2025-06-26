from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Limit


@receiver(post_save, sender=User)
def create_user_limit(sender, instance, created, **kwargs):
    """
    當用戶被創建時，自動為該用戶創建 Limit 記錄
    """
    if created:
        # 檢查是否已經有 Limit 記錄，如果沒有則創建
        if not hasattr(instance, 'limit'):
            Limit.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_limit(sender, instance, **kwargs):
    """
    當用戶被保存時，確保 Limit 記錄存在
    """
    if hasattr(instance, 'limit'):
        instance.limit.save()
    else:
        # 如果沒有 Limit 記錄，則創建一個
        Limit.objects.get_or_create(user=instance) 