from django.contrib import admin
from .models import Limit

# Register your models here.

@admin.register(Limit)
class LimitAdmin(admin.ModelAdmin):
    """
    Limit 模型的 Admin 配置
    """
    list_display = ['user', 'chat_limit_per_day', 'private_source_limit', 'file_limit_per_source', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('使用者資訊', {
            'fields': ('user',)
        }),
        ('使用限制', {
            'fields': ('chat_limit_per_day', 'private_source_limit', 'file_limit_per_source')
        }),
        ('時間資訊', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
