from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.SourceListView.as_view(), name='source_list'),
    path('create/', views.SourceCreateView.as_view(), name='source_create'),
    path('<int:pk>/', views.SourceDetailView.as_view(), name='source_detail'),
    path('<int:pk>/upload/', views.SourceUploadView.as_view(), name='source_upload'),
] 