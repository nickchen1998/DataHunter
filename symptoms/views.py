from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.models import User
from symptoms.models import Symptom


# Create your views here.
class SymptomListView(ListView):
    template_name = 'symptoms.html'
    context_object_name = 'symptoms'
    queryset = Symptom.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context variables here
        return context
