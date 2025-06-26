from django.contrib import admin
from .models import Limit, Profile

# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Profile 模型的 Admin 配置
    """
    list_display = ['user', 'is_collaborator', 'created_at', 'updated_at']
    list_filter = ['is_collaborator', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('使用者資訊', {
            'fields': ('user',)
        }),
        ('權限設定', {
            'fields': ('is_collaborator',)
        }),
        ('時間資訊', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


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
