from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.views import View
from crawlers.models import Symptom
from home.mixins import UserPlanContextMixin
from langchain_openai import ChatOpenAI
import json
import random

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
        try:
            all_symptoms = list(Symptom.objects.order_by('-id').values_list(
                'question', flat=True
            ).distinct()[:20])
            
            if not all_symptoms:
                return JsonResponse({
                    'success': False,
                    'message': '目前無法生成建議問題'
                })
            
            sample_size = min(len(all_symptoms), random.randint(4, 8))
            selected_symptoms = random.sample(all_symptoms, sample_size)
            
            symptoms_text = "\n".join([f"- {q[:100]}..." if len(q) > 100 else f"- {q}" for q in selected_symptoms])
            
            variety_prompts = [
                "生成4個多樣化的健康問題",
                "創建4個不同類型的醫療諮詢問題", 
                "設計4個涵蓋不同健康領域的問題",
                "產生4個適合一般人詢問的健康問題"
            ]
            
            selected_prompt = random.choice(variety_prompts)
            
            prompt = f"""基於以下醫療症狀諮詢參考資料，請{selected_prompt}，這些問題應該：

1. 簡潔明瞭（不超過20個字）
2. 主題多樣化，避免重複相似領域
3. 適合一般民眾詢問
4. 與健康醫療相關
5. 能引發有意義的醫療對話

參考資料：
{symptoms_text}

要求：請確保4個問題涵蓋不同的健康主題，避免過度集中在同一疾病或症狀上。
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
                if line and not line.startswith('#') and len(line) <= 50:
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
        
        