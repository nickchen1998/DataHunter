from django.urls import path
from . import views

urlpatterns = [
    path('agree-to-terms/', views.agree_to_terms, name='agree_to_terms'),
    path('check-terms-status/', views.check_terms_status, name='check_terms_status'),
] 