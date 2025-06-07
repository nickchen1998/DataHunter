from django.views.generic import ListView
from symptoms.models import Symptom
from django.http import JsonResponse
from symptoms.serializers import SymptomSerializer

from langchain_openai import OpenAIEmbeddings
from pgvector.django import CosineDistance


class SymptomListView(ListView):
    template_name = 'symptoms.html'
    context_object_name = 'symptoms'
    queryset = Symptom.objects.order_by("-question_time").all()
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        if department := self.request.GET.get('department'):
            queryset = queryset.filter(department__icontains=department)

        if gender := self.request.GET.get('gender'):
            queryset = queryset.filter(gender=gender)

        if question := self.request.GET.get('question'):
            queryset = queryset.filter(question__icontains=question)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        context['department'] = self.request.GET.get('department', '')
        context['gender'] = self.request.GET.get('gender', '')
        context['question'] = self.request.GET.get('question', '')

        # Add distinct departments for the dropdown filter
        context['departments'] = Symptom.objects.values_list('department', flat=True).distinct().order_by('department')

        # Add distinct genders for the dropdown filter
        context['genders'] = Symptom.objects.values_list('gender', flat=True).distinct().order_by('gender')

        return context

    def render_to_response(self, context, **response_kwargs):
        if (self.request.headers.get('Accept') == 'application/json' or
                self.request.GET.get('format') == 'json'):
            data = {
                'count': context['page_obj'].paginator.count,
                'total_pages': context['page_obj'].paginator.num_pages,
                'current_page': context['page_obj'].number,
                'has_next': context['page_obj'].has_next(),
                'has_previous': context['page_obj'].has_previous(),
                'results': SymptomSerializer(context['symptoms'], many=True).data,  # 當頁資料
            }

            return JsonResponse(
                data,
                safe=False,
                json_dumps_params={'ensure_ascii': False},
                content_type='application/json; charset=utf-8',
            )
        else:
            return super().render_to_response(context, **response_kwargs)
