from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from crawlers.models import Dataset, ASSOCIATED_CATEGORIES_DATABASE_NAME
from home.mixins import UserPlanContextMixin
from langchain_openai import ChatOpenAI
import random
import psycopg2
import psycopg2.extras


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
        try:
            datasets = list(Dataset.objects.prefetch_related('file_set').order_by('?')[:4])
            
            if not datasets:
                return JsonResponse({
                    'success': False,
                    'message': '目前無法生成建議問題'
                })

            dataset_info = []
            for dataset in datasets:
                files = dataset.file_set.all()[:2]
                file_info = []
                
                for file in files:
                    try:
                        sample_data = self._get_sample_data(file.database_name, file.table_name)
                        column_info = []
                        if file.column_mapping_list:
                            column_info = [f"{col[0]}: {col[1]}" for col in file.column_mapping_list[:3]]
                        
                        file_info.append({
                            'table_name': file.table_name,
                            'columns': column_info,
                            'sample_data': sample_data
                        })
                    except Exception as e:
                        file_info.append({
                            'table_name': file.table_name,
                            'columns': [f"{col[0]}: {col[1]}" for col in file.column_mapping_list[:3]] if file.column_mapping_list else [],
                            'sample_data': {}
                        })
                
                dataset_info.append({
                    'name': dataset.name,
                    'category': dataset.category,
                    'description': dataset.description[:200] if dataset.description else '',
                    'files': file_info
                })

            variety_prompts = [
                "生成4個關於政府資料查詢的問題",
                "創建4個不同類型的政府開放資料問題",
                "設計4個涵蓋不同政府服務領域的問題",
                "產生4個適合查詢政府資料的問題"
            ]
            
            selected_prompt = random.choice(variety_prompts)
            
            dataset_text = ""
            for d in dataset_info:
                dataset_text += f"資料集：{d['name']} (分類：{d['category']})\n"
                dataset_text += f"描述：{d['description']}\n"
                for f in d['files']:
                    dataset_text += f"資料表：{f['table_name']}\n"
                    if f['sample_data']:
                        sample_values = list(f['sample_data'].values())[:3]
                        dataset_text += f"範例資料：{', '.join(str(v) for v in sample_values)}\n"
                dataset_text += "\n"

            prompt = f"""基於以下政府開放資料集資訊，請{selected_prompt}，這些問題應該：

1. 簡潔明瞭（不超過25個字）
2. 主題多樣化，涵蓋不同政府服務領域
3. 適合一般民眾查詢政府資料
4. 與政府開放資料相關
5. 能引發有意義的資料查詢
6. 可以基於實際的資料內容提問

參考資料集及範例：
{dataset_text}

要求：請確保4個問題涵蓋不同的政府服務主題，避免過度集中在同一領域。
請直接返回4個問題，每行一個問題，不需要編號或其他格式："""

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.8,
                model_kwargs={
                    "seed": random.randint(1, 10000)
                }
            )
            response = llm.invoke(prompt)
            
            questions = []
            for line in response.content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and len(line) <= 60:
                    line = line.lstrip('0123456789.-) ')
                    if line:
                        questions.append(line)
            
            unique_questions = []
            for q in questions:
                is_similar = False
                for existing in unique_questions:
                    q_words = set(q.replace('？', '').replace('?', '').split())
                    existing_words = set(existing.replace('？', '').replace('?', '').split())
                    if len(q_words & existing_words) / max(len(q_words), len(existing_words)) > 0.5:
                        is_similar = True
                        break
                
                if not is_similar:
                    unique_questions.append(q)
            
            final_questions = unique_questions[:4] if unique_questions else []
            
            if final_questions:
                return JsonResponse({
                    'success': True,
                    'suggestions': final_questions
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '目前無法生成建議問題'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': '建議問題生成失敗'
            })
    
    def _get_sample_data(self, database_name, table_name):
        """從指定的資料庫和資料表中獲取第一筆數據"""
        try:
            db_config = settings.DATABASES['default']
            
            db_uri = f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}@{db_config['HOST']}:{db_config['PORT']}/{database_name}"
            
            conn = psycopg2.connect(db_uri)
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 1')
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                else:
                    return {}
                    
        except Exception as e:
            return {}
        finally:
            if 'conn' in locals():
                conn.close()
        