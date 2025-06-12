from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import UserAPIKey


@admin.register(UserAPIKey)
class UserAPIKeyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'user', 
        'formatted_key', 
        'is_active', 
        'expires_status',
        'last_used_at', 
        'created_at'
    ]
    list_filter = [
        'is_active', 
        'created_at', 
        'expires_at',
        'user'
    ]
    search_fields = [
        'name', 
        'user__username', 
        'user__email'
    ]
    readonly_fields = [
        'id', 
        'prefix', 
        'created_at', 
        'updated_at',
        'last_used_at'
    ]
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('user', 'name', 'is_active')
        }),
        ('時間設定', {
            'fields': ('expires_at',)
        }),
        ('使用記錄', {
            'fields': ('last_used_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('系統資訊', {
            'fields': ('id', 'prefix'),
            'classes': ('collapse',)
        }),
    )

    def formatted_key(self, obj):
        """格式化顯示 API Key（只顯示前後幾位）"""
        if obj.prefix:
            return f"{obj.prefix}...{obj.id}"
        return "未產生"
    formatted_key.short_description = "API Key"

    def expires_status(self, obj):
        """顯示過期狀態"""
        if not obj.expires_at:
            return format_html('<span style="color: green;">永不過期</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">已過期</span>')
        else:
            days_left = (obj.expires_at - timezone.now()).days
            if days_left <= 7:
                return format_html(
                    '<span style="color: orange;">還有 {} 天過期</span>', 
                    days_left
                )
            else:
                return format_html(
                    '<span style="color: green;">還有 {} 天過期</span>', 
                    days_left
                )
    expires_status.short_description = "過期狀態"

    def get_queryset(self, request):
        """優化查詢，預載使用者資訊"""
        return super().get_queryset(request).select_related('user')
