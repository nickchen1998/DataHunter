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
    list_display = ['id', 'session', 'user', 'sender', 'content_type', 'tool_name', 'created_at']
    list_filter = ['sender', 'content_type', 'created_at', 'tool_name']
    search_fields = ['user__email', 'user__username', 'text', 'tool_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('session', 'user', 'sender', 'content_type', 'created_at')
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
