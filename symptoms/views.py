from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.models import User
from symptoms.models import Symptom
from django.core.paginator import Paginator


# Create your views here.
class SymptomListView(ListView):
    template_name = 'symptoms.html'
    context_object_name = 'symptoms'
    queryset = Symptom.objects.order_by("-question_time").all()
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # print(context.values())

        return context
