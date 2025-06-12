from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from symptoms.models import Symptom
from symptoms.serializers import SymptomSerializer
from symptoms.utils import build_symptom_queryset
from DataHunter.paginator import BasePagination


@method_decorator(never_cache, name='dispatch')
class SymptomListView(LoginRequiredMixin, ListView):
    template_name = 'symptoms.html'
    context_object_name = 'symptoms'
    queryset = Symptom.objects.all()
    paginate_by = 10
    login_url = '/login/'  # 未登入時重定向的 URL

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


class SymptomSearchAPIView(APIView):
    pagination_class = BasePagination
    
    def post(self, request):
        try:
            serializer = SymptomSerializer(data=request.body, context={'request': request})
            if not serializer.is_valid():
                return Response({
                    'error': '參數驗證失敗',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            request._pagination_data = {
                'page': validated_data.get('page', 1),
                'page_size': validated_data.get('page_size', 10)
            }
            
            queryset = build_symptom_queryset(
                department=validated_data.get('department'),
                gender=validated_data.get('gender'),
                question=validated_data.get('question')
            )
            
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)
            
            if page is not None:
                serializer = SymptomSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = SymptomSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': '伺服器內部錯誤',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    