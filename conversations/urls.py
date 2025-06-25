from django.urls import path
from . import views

app_name = 'conversations'

urlpatterns = [
    path('api/messages/<int:message_id>/tool-calls/', views.get_message_tool_calls, name='message_tool_calls'),
] 