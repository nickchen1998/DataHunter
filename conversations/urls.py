from django.urls import path
from . import views

app_name = 'conversations'

urlpatterns = [
    path('history/', views.get_conversation_history, name='history'),
] 