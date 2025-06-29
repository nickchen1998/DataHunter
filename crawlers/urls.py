from django.urls import path
from .views import GovDataDatasetListView, SymptomListView, SymptomSuggestView

urlpatterns = [
    path('gov-data/list/', GovDataDatasetListView.as_view(), name='gov_data_list'),
    path('symptoms/list/', SymptomListView.as_view(), name='symptom_list'),
    path('api/suggestions/', SymptomSuggestView.as_view(), name='symptom_suggestions'),
] 