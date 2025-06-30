from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.views import View
from crawlers.models import Symptom
from home.mixins import UserPlanContextMixin


@method_decorator(never_cache, name='dispatch')
class SymptomListView(LoginRequiredMixin, UserPlanContextMixin, ListView):
    template_name = 'symptoms.html'
    context_object_name = 'symptoms'
    queryset = Symptom.objects.all()
    paginate_by = 10
    login_url = '/login/'

    def get_queryset(self):
        department = self.request.GET.get('department')
        gender = self.request.GET.get('gender')
        question = self.request.GET.get('question')
        
        return Symptom.objects.build_queryset(
            department=department, 
            gender=gender, 
            question=question
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        context['department'] = self.request.GET.get('department', '')
        context['gender'] = self.request.GET.get('gender', '')
        context['question'] = self.request.GET.get('question', '')
        context['departments'] = Symptom.objects.values_list('department', flat=True).distinct().order_by('department')
        context['genders'] = Symptom.objects.values_list('gender', flat=True).distinct().order_by('gender')
          
        return context 


class SymptomSuggestView(LoginRequiredMixin, View):
    
    def get(self, request):
        """使用重構後的工具生成症狀建議問題"""
        from utils.question_suggestions import generate_symptom_suggestions
        
        return generate_symptom_suggestions()
        
        