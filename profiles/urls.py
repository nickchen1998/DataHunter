from django.urls import path
from .views import ProfileView, UserAPIKeyListView, UserAPIKeyDetailView

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
    path('api-keys/', UserAPIKeyListView.as_view(), name='api_keys_list'),
    path('api-keys/<str:prefix>/', UserAPIKeyDetailView.as_view(), name='api_key_detail'),
] 