from django.db import models
from django.contrib.auth import get_user_model
import uuid

# 共用內容型態 Enum
class ContentTypeChoices(models.TextChoices):
    TEXT = 'text', 'Text'
    AUDIO = 'audio', 'Audio'
    IMAGE = 'image', 'Image'
    VIDEO = 'video', 'Video'
    FILE = 'file', 'File'


# 共用 sender Enum
class SenderChoices(models.TextChoices):
    USER = 'user', 'User'
    AI = 'ai', 'AI'
    TOOL = 'tool', 'Tool'


User = get_user_model()


class Session(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"Session {self.session_uuid} ({self.title})"

class Message(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL)
    
    sender = models.CharField(
        max_length=16,
        choices=SenderChoices.choices,
        default=SenderChoices.USER,
    )
    content_type = models.CharField(
        max_length=16,
        choices=ContentTypeChoices.choices,
        default=ContentTypeChoices.TEXT,
    )
    text = models.TextField(blank=True, null=True, default=None)
    file_url = models.URLField(blank=True, null=True, default=None)
    file_path = models.CharField(max_length=256, blank=True, null=True, default=None)

    # Tool 專屬欄位（sender=TOOL 時才需填寫）
    tool_name = models.CharField(max_length=64, blank=True)
    tool_keywords = models.JSONField(default=list, blank=True)  # 儲存 keyword 清單

    created_at = models.DateTimeField(auto_now_add=True)
