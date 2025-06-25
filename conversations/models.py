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

    class Meta:
        verbose_name = "對話會話"
        verbose_name_plural = "對話會話"

    def __str__(self):
        user_info = self.user.email if self.user else "匿名用戶"
        return f"{user_info} - {self.title or str(self.session_uuid)[:8]}"

    @classmethod
    def get_or_create_user_session(cls, user):
        """取得或建立使用者的 session（目前每位使用者只有一個 session）"""
        session, created = cls.objects.get_or_create(
            user=user,
            defaults={'title': 'default'}
        )
        return session


class Message(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
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

    # 軟刪除欄位
    is_deleted = models.BooleanField(default=False, help_text="軟刪除標記")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "對話訊息"
        verbose_name_plural = "對話訊息"
        ordering = ['-updated_at']

    def __str__(self):
        sender_display = self.get_sender_display()
        preview = (self.text[:50] + '...') if self.text and len(self.text) > 50 else (self.text or '')
        if self.sender == SenderChoices.TOOL:
            return f"[{sender_display}] {self.tool_name}: {preview}"
        return f"[{sender_display}] {preview}"

    def soft_delete(self):
        """軟刪除訊息"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    @classmethod
    def clear_conversation(cls, session):
        """清空對話（軟刪除所有訊息）"""
        return cls.objects.filter(session=session, is_deleted=False).update(is_deleted=True)

    @classmethod
    def create_user_message(cls, session, user, text):
        """建立使用者訊息記錄"""
        return cls.objects.create(
            session=session,
            user=user,
            sender=SenderChoices.USER,
            content_type=ContentTypeChoices.TEXT,
            text=text
        )

    @classmethod
    def create_ai_message(cls, session, user, text):
        """建立 AI 回覆訊息記錄"""
        return cls.objects.create(
            session=session,
            user=user,
            sender=SenderChoices.AI,
            content_type=ContentTypeChoices.TEXT,
            text=text
        )

    @classmethod
    def create_tool_message(cls, session, user, tool_name, tool_params, tool_result=None):
        """建立 Tool 調用訊息記錄"""
        return cls.objects.create(
            session=session,
            user=user,
            sender=SenderChoices.TOOL,
            content_type=ContentTypeChoices.TEXT,
            tool_name=tool_name,
            tool_keywords=tool_params,
            text=tool_result
        )
