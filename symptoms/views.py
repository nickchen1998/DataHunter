from django.views.generic import ListView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from symptoms.models import Symptom
from django.http import JsonResponse
from symptoms.serializers import SymptomSerializer
from utils.search_utils import hybrid_search_with_rerank
from django.core.paginator import Paginator


def build_symptom_queryset(department=None, gender=None, question=None):
    queryset = Symptom.objects.all()
    
    if department:
        queryset = queryset.filter(department__icontains=department)
    
    if gender:
        queryset = queryset.filter(gender=gender)
    
    if question:
        queryset = hybrid_search_with_rerank(
            queryset=queryset,
            vector_field_name="question_embeddings",
            text_field_name="question",
            original_question=question,
        )
    else:
        queryset = queryset.order_by("-question_time")
    
    return queryset


class SymptomListView(ListView):
    template_name = 'symptoms.html'
    context_object_name = 'symptoms'
    queryset = Symptom.objects.all()
    paginate_by = 10

    def get_queryset(self):
        department = self.request.GET.get('department')
        gender = self.request.GET.get('gender')
        original_question = self.request.GET.get('question')
        
        return build_symptom_queryset(department, gender, original_question)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        context['department'] = self.request.GET.get('department', '')
        context['gender'] = self.request.GET.get('gender', '')
        context['question'] = self.request.GET.get('question', '')
        context['departments'] = Symptom.objects.values_list('department', flat=True).distinct().order_by('department')
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
                'results': SymptomSerializer(context['symptoms'], many=True).data,
            }

            return JsonResponse(
                data,
                safe=False,
                json_dumps_params={'ensure_ascii': False},
                content_type='application/json; charset=utf-8',
            )
        else:
            return super().render_to_response(context, **response_kwargs)


class SymptomSearchAPIView(APIView):
    
    def post(self, request):
        try:
            serializer = SymptomSerializer(data=request.body, context={'request': request})
            if not serializer.is_valid():
                return Response({
                    'error': '參數驗證失敗',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            queryset = build_symptom_queryset(
                department=validated_data.get('department'),
                gender=validated_data.get('gender'),
                question=validated_data.get('question')
            )
            
            page = validated_data.get('page', 1)
            page_size = validated_data.get('page_size', 10)
            
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            response_data = serializer.create_response(queryset, page_obj)
            
            return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': '伺服器內部錯誤',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    