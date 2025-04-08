from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.models import User


# Create your views here.
class SymptomListView(ListView):
    model = User  # Replace with your actual model
    template_name = 'base.html'  # Replace with your actual template
    context_object_name = 'symptoms'  # Name of the variable to be used in the template
    paginate_by = 10  # Number of items per page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context variables here
        return context
