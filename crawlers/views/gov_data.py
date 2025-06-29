from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from crawlers.models import Dataset, ASSOCIATED_CATEGORIES_DATABASE_NAME
from home.mixins import UserPlanContextMixin


@method_decorator(never_cache, name='dispatch')
class GovDataDatasetListView(LoginRequiredMixin, UserPlanContextMixin, ListView):
    model = Dataset
    template_name = 'gov_datas.html'
    context_object_name = 'datasets'
    paginate_by = 20
    login_url = '/login/'  # 未登入時重定向的 URL

    def get_queryset(self):
        category = self.request.GET.get('category')
        description = self.request.GET.get('description')
        name = self.request.GET.get('name')
        upload_start = self.request.GET.get('upload_start')
        upload_end = self.request.GET.get('upload_end')
        update_start = self.request.GET.get('update_start')
        update_end = self.request.GET.get('update_end')
        
        queryset = Dataset.objects.build_queryset(
            category=category,
            description=description,
            name=name,
            upload_start=upload_start,
            upload_end=upload_end,
            update_start=update_start,
            update_end=update_end
        )
        
        # 預載入檔案關聯以提高效能
        return queryset.prefetch_related('file_set')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['categories'] = ASSOCIATED_CATEGORIES_DATABASE_NAME.keys()
        
        # 保存當前過濾條件
        context['category'] = self.request.GET.get('category', '')
        context['description'] = self.request.GET.get('description', '')
        context['name'] = self.request.GET.get('name', '')
        context['upload_start'] = self.request.GET.get('upload_start', '')
        context['upload_end'] = self.request.GET.get('upload_end', '')
        context['update_start'] = self.request.GET.get('update_start', '')
        context['update_end'] = self.request.GET.get('update_end', '')
        context['request_path'] = self.request.path
        
        return context

class GovDataSuggestView(LoginRequiredMixin, View):
    def get(self, request):
        """
        隨機取得四個 Dataset 並且讀取其底下的 File 以及其對應的資料表的第一行資料，
        將 Dataset 資訊以及第一行資料作為生成建議問題的素材
        """
        