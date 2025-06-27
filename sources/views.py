from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from home.mixins import UserPlanContextMixin


class SourceListView(LoginRequiredMixin, UserPlanContextMixin, ListView):
    """自建資料源列表視圖"""
    template_name = 'sources/source_list.html'
    context_object_name = 'sources'
    paginate_by = 10
    
    def get_queryset(self):
        # 使用假資料
        fake_sources = [
            {'id': 1, 'name': '產品銷售報告', 'description': '2024年第一季度產品銷售數據分析', 'file_count': 5, 'created_at': '2024-01-15'},
            {'id': 2, 'name': '客戶滿意度調查', 'description': '客戶對服務品質的滿意度調查結果', 'file_count': 3, 'created_at': '2024-02-20'},
            {'id': 3, 'name': '員工培訓資料', 'description': '新進員工培訓手冊和教材', 'file_count': 8, 'created_at': '2024-03-10'},
            {'id': 4, 'name': '市場分析報告', 'description': '競爭對手分析和市場趨勢研究', 'file_count': 2, 'created_at': '2024-03-25'},
            {'id': 5, 'name': '技術文件', 'description': 'API 文件和系統架構說明', 'file_count': 12, 'created_at': '2024-04-05'},
        ]
        
        return fake_sources
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        return context


class SourceCreateView(LoginRequiredMixin, UserPlanContextMixin, TemplateView):
    """建立新資料源視圖"""
    template_name = 'sources/source_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        return context
    
    def post(self, request, *args, **kwargs):
        # 處理表單提交
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name and description:
            messages.success(request, f'資料源「{name}」建立成功！')
            # 重定向到假的詳細頁面
            return redirect('source_detail', pk=1)
        else:
            messages.error(request, '請填寫所有必要欄位。')
            return self.get(request, *args, **kwargs)


class SourceDetailView(LoginRequiredMixin, UserPlanContextMixin, TemplateView):
    """資料源詳細視圖"""
    template_name = 'sources/source_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        
        # 假資料
        source_id = kwargs.get('pk')
        context['source'] = {
            'id': source_id,
            'name': '產品銷售報告',
            'description': '2024年第一季度產品銷售數據分析',
            'created_at': '2024-01-15',
            'file_count': 5
        }
        
        # 假的檔案列表
        context['files'] = [
            {'id': 1, 'name': '銷售報告_Q1.pdf', 'size': '2.3 MB', 'uploaded_at': '2024-01-15'},
            {'id': 2, 'name': '產品分析_202401.xlsx', 'size': '1.8 MB', 'uploaded_at': '2024-01-16'},
            {'id': 3, 'name': '客戶清單.csv', 'size': '0.5 MB', 'uploaded_at': '2024-01-17'},
            {'id': 4, 'name': '營收統計.docx', 'size': '1.2 MB', 'uploaded_at': '2024-01-18'},
            {'id': 5, 'name': '分析結果.pptx', 'size': '3.1 MB', 'uploaded_at': '2024-01-19'},
        ]
        
        return context


class SourceUploadView(LoginRequiredMixin, UserPlanContextMixin, TemplateView):
    """檔案上傳視圖"""
    template_name = 'sources/source_upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        
        # 假資料
        source_id = kwargs.get('pk')
        context['source'] = {
            'id': source_id,
            'name': '產品銷售報告',
            'description': '2024年第一季度產品銷售數據分析',
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        # 處理檔案上傳
        uploaded_files = request.FILES.getlist('files')
        
        if uploaded_files:
            file_names = [file.name for file in uploaded_files]
            messages.success(request, f'成功上傳 {len(uploaded_files)} 個檔案：{", ".join(file_names)}')
            return redirect('source_detail', pk=kwargs.get('pk'))
        else:
            messages.error(request, '請選擇要上傳的檔案。')
            return self.get(request, *args, **kwargs)
