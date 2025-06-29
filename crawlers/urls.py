from django.urls import path
from .views import GovDataDatasetListView, SymptomListView, SymptomSuggestView
from .views.gov_data import GovDataSuggestView

urlpatterns = [
    path('gov-data/list/', GovDataDatasetListView.as_view(), name='gov_data_list'),
    path('symptoms/list/', SymptomListView.as_view(), name='symptom_list'),
    path('api/symptoms-suggestions/', SymptomSuggestView.as_view(), name='symptom_suggestions'),
    path('api/gov-data-suggestions/', GovDataSuggestView.as_view(), name='gov_data_suggestions'),
] 