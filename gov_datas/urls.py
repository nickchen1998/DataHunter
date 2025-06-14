from django.urls import path
from .views import GovDataDatasetListView

urlpatterns = [
    path('list/', GovDataDatasetListView.as_view(), name='gov_data_list'),
] 