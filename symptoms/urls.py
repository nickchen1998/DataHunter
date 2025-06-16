from django.urls import path
from symptoms import views

urlpatterns = [
    path('list/', views.SymptomListView.as_view(), name='symptom_list'),
]