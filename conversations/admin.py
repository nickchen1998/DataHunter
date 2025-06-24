from django.contrib import admin
from .models import Session, Message


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_uuid', 'user', 'title', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'user__username', 'title']
    readonly_fields = ['session_uuid', 'created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'user', 'sender', 'content_type', 'tool_name', 'is_deleted', 'created_at']
    list_filter = ['sender', 'content_type', 'is_deleted', 'created_at', 'tool_name']
    search_fields = ['user__email', 'user__username', 'text', 'tool_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('session', 'user', 'sender', 'content_type', 'is_deleted', 'created_at')
        }),
        ('內容', {
            'fields': ('text', 'file_url', 'file_path')
        }),
        ('工具相關', {
            'fields': ('tool_name', 'tool_keywords'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'user')

    def restore_messages(self, request, queryset):
        """恢復軟刪除的訊息"""
        updated = queryset.filter(is_deleted=True).update(is_deleted=False)
        self.message_user(request, f'已恢復 {updated} 筆訊息')
    restore_messages.short_description = "恢復選中的訊息"

    def soft_delete_messages(self, request, queryset):
        """軟刪除訊息"""
        updated = queryset.filter(is_deleted=False).update(is_deleted=True)
        self.message_user(request, f'已軟刪除 {updated} 筆訊息')
    soft_delete_messages.short_description = "軟刪除選中的訊息"

    actions = ['restore_messages', 'soft_delete_messages']
