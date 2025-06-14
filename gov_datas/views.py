from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Q
from datetime import datetime
from .models import Dataset
from .utils import build_dataset_queryset

# Create your views here.

class GovDataDatasetListView(ListView):
    model = Dataset
    template_name = 'gov_datas.html'
    context_object_name = 'datasets'
    paginate_by = 20

    def get_queryset(self):
        category = self.request.GET.get('category')
        description = self.request.GET.get('description')
        name = self.request.GET.get('name')
        upload_start = self.request.GET.get('upload_start')
        upload_end = self.request.GET.get('upload_end')
        update_start = self.request.GET.get('update_start')
        update_end = self.request.GET.get('update_end')
        
        queryset = build_dataset_queryset(
            category=category,
            description=description,
            name=name,
            upload_start=upload_start,
            upload_end=upload_end,
            update_start=update_start,
            update_end=update_end
        )
        
        # 預載入檔案關聯以提高效能
        return queryset.prefetch_related('files')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 使用 group by 獲取服務分類選項
        categories = Dataset.objects.values('category').distinct().order_by('category')
        context['categories'] = [cat['category'] for cat in categories if cat['category']]
        
        # 保存當前過濾條件
        context['category'] = self.request.GET.get('category', '')
        context['description'] = self.request.GET.get('description', '')
        context['name'] = self.request.GET.get('name', '')
        context['upload_start'] = self.request.GET.get('upload_start', '')
        context['upload_end'] = self.request.GET.get('upload_end', '')
        context['update_start'] = self.request.GET.get('update_start', '')
        context['update_end'] = self.request.GET.get('update_end', '')
        context['request_path'] = self.request.path
        
        # 添加總數統計
        context['total_count'] = Dataset.objects.count()
        
        return context
