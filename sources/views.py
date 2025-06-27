from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import Http404
from home.mixins import UserPlanContextMixin
from .models import Source, SourceFile
from profiles.models import Limit, Profile


class SourceListView(LoginRequiredMixin, UserPlanContextMixin, ListView):
    """自建資料源列表視圖"""
    model = Source
    template_name = 'sources/source_list.html'
    context_object_name = 'sources'
    paginate_by = 10
    
    def get_queryset(self):
        # 只顯示當前用戶的非刪除資料源
        return Source.objects.filter(
            user=self.request.user, 
            is_deleted=False
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        
        # 獲取用戶的限制資訊
        limit, _ = Limit.objects.get_or_create(user=self.request.user)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        
        # 計算私有資料源數量
        private_source_count = Source.objects.filter(
            user=self.request.user, 
            is_deleted=False
        ).count()
        
        # 檢查用戶權限層級
        is_superuser = self.request.user.is_superuser
        has_unlimited_source = is_superuser
        
        # 檢查是否可以建立新資料源
        can_create_source = has_unlimited_source or private_source_count < limit.private_source_limit
        
        context.update({
            'private_source_count': private_source_count,
            'private_source_limit': limit.private_source_limit,
            'remaining_source_count': max(0, limit.private_source_limit - private_source_count) if not has_unlimited_source else 999,
            'has_unlimited_source': has_unlimited_source,
            'can_create_source': can_create_source,
        })
        
        return context


class SourceCreateView(LoginRequiredMixin, UserPlanContextMixin, TemplateView):
    """建立新資料源視圖"""
    template_name = 'sources/source_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        
        # 檢查是否可以建立新資料源
        limit, _ = Limit.objects.get_or_create(user=self.request.user)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        
        private_source_count = Source.objects.filter(
            user=self.request.user, 
            is_deleted=False
        ).count()
        
        is_superuser = self.request.user.is_superuser
        has_unlimited_source = is_superuser
        can_create_source = has_unlimited_source or private_source_count < limit.private_source_limit
        
        context.update({
            'private_source_count': private_source_count,
            'private_source_limit': limit.private_source_limit,
            'remaining_source_count': max(0, limit.private_source_limit - private_source_count) if not has_unlimited_source else 999,
            'has_unlimited_source': has_unlimited_source,
            'can_create_source': can_create_source,
        })
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        # 檢查是否可以建立新資料源
        limit, _ = Limit.objects.get_or_create(user=request.user)
        private_source_count = Source.objects.filter(
            user=request.user, 
            is_deleted=False
        ).count()
        
        is_superuser = request.user.is_superuser
        has_unlimited_source = is_superuser
        can_create_source = has_unlimited_source or private_source_count < limit.private_source_limit
        
        if not can_create_source:
            messages.error(request, f'您已達到私有資料源數量上限（{limit.private_source_limit} 個）。請刪除現有資料源或聯繫管理員提升限制。')
            return redirect('source_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        # 再次檢查限制（防止併發建立）
        limit, _ = Limit.objects.get_or_create(user=request.user)
        private_source_count = Source.objects.filter(
            user=request.user, 
            is_deleted=False
        ).count()
        
        is_superuser = request.user.is_superuser
        has_unlimited_source = is_superuser
        can_create_source = has_unlimited_source or private_source_count < limit.private_source_limit
        
        if not can_create_source:
            messages.error(request, f'您已達到私有資料源數量上限（{limit.private_source_limit} 個）。請刪除現有資料源或聯繫管理員提升限制。')
            return redirect('source_list')
        
        # 處理表單提交
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name or not description:
            messages.error(request, '請填寫所有必要欄位。')
            return self.get(request, *args, **kwargs)
        
        # 檢查名稱是否重複
        if Source.objects.filter(user=request.user, name=name, is_deleted=False).exists():
            messages.error(request, f'資料源名稱「{name}」已存在，請使用不同的名稱。')
            return self.get(request, *args, **kwargs)
        
        # 建立資料源
        source = Source.objects.create(
            user=request.user,
            name=name,
            description=description,
            is_public=False  # 預設為私有
        )
        
        messages.success(request, f'資料源「{name}」建立成功！')
        return redirect('source_detail', pk=source.id)


class SourceDetailView(LoginRequiredMixin, UserPlanContextMixin, DetailView):
    """資料源詳細視圖"""
    model = Source
    template_name = 'sources/source_detail.html'
    context_object_name = 'source'
    
    def get_object(self, queryset=None):
        # 只允許用戶查看自己的資料源
        source = get_object_or_404(
            Source, 
            pk=self.kwargs['pk'], 
            user=self.request.user, 
            is_deleted=False
        )
        return source
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        
        source = self.get_object()
        
        # 獲取真實的檔案列表（目前還是假資料，因為用戶要求檔案部分維持假資料）
        fake_files = [
            {'id': 1, 'name': '銷售報告_Q1.pdf', 'size': '2.3 MB', 'uploaded_at': '2024-01-15'},
            {'id': 2, 'name': '產品分析_202401.xlsx', 'size': '1.8 MB', 'uploaded_at': '2024-01-16'},
            {'id': 3, 'name': '客戶清單.csv', 'size': '0.5 MB', 'uploaded_at': '2024-01-17'},
            {'id': 4, 'name': '營收統計.docx', 'size': '1.2 MB', 'uploaded_at': '2024-01-18'},
            {'id': 5, 'name': '分析結果.pptx', 'size': '3.1 MB', 'uploaded_at': '2024-01-19'},
        ]
        
        context['files'] = fake_files
        context['file_count'] = len(fake_files)
        
        return context


class SourceEditView(LoginRequiredMixin, UserPlanContextMixin, TemplateView):
    """編輯資料源視圖"""
    template_name = 'sources/source_edit.html'
    
    def get_source(self):
        # 只允許用戶編輯自己的資料源
        return get_object_or_404(
            Source, 
            pk=self.kwargs['pk'], 
            user=self.request.user, 
            is_deleted=False
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        context['source'] = self.get_source()
        return context
    
    def post(self, request, *args, **kwargs):
        source = self.get_source()
        
        # 處理表單提交
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name or not description:
            messages.error(request, '請填寫所有必要欄位。')
            return self.get(request, *args, **kwargs)
        
        # 檢查名稱是否重複（排除自己）
        if Source.objects.filter(
            user=request.user, 
            name=name, 
            is_deleted=False
        ).exclude(pk=source.pk).exists():
            messages.error(request, f'資料源名稱「{name}」已存在，請使用不同的名稱。')
            return self.get(request, *args, **kwargs)
        
        # 更新資料源
        source.name = name
        source.description = description
        source.save()
        
        messages.success(request, f'資料源「{name}」更新成功！')
        return redirect('source_detail', pk=source.id)


class SourceDeleteView(LoginRequiredMixin, UserPlanContextMixin, TemplateView):
    """刪除資料源視圖"""
    template_name = 'sources/source_delete.html'
    
    def get_source(self):
        # 只允許用戶刪除自己的資料源
        return get_object_or_404(
            Source, 
            pk=self.kwargs['pk'], 
            user=self.request.user, 
            is_deleted=False
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        context['source'] = self.get_source()
        return context
    
    def post(self, request, *args, **kwargs):
        source = self.get_source()
        
        # 軟刪除資料源
        source.soft_delete()
        
        messages.success(request, f'資料源「{source.name}」已成功刪除。')
        return redirect('source_list')


class SourceUploadView(LoginRequiredMixin, UserPlanContextMixin, TemplateView):
    """檔案上傳視圖"""
    template_name = 'sources/source_upload.html'
    
    def get_source(self):
        # 只允許用戶操作自己的資料源
        return get_object_or_404(
            Source, 
            pk=self.kwargs['pk'], 
            user=self.request.user, 
            is_deleted=False
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_path'] = self.request.path
        context['source'] = self.get_source()
        
        # 檢查檔案上傳限制
        limit, _ = Limit.objects.get_or_create(user=self.request.user)
        is_superuser = self.request.user.is_superuser
        has_unlimited_files = is_superuser
        
        # 獲取當前資料源的檔案數量（使用假資料數量）
        current_file_count = 5  # 假資料中有5個檔案
        
        can_upload_files = has_unlimited_files or current_file_count < limit.file_limit_per_source
        
        context.update({
            'current_file_count': current_file_count,
            'file_limit_per_source': limit.file_limit_per_source,
            'remaining_file_count': max(0, limit.file_limit_per_source - current_file_count) if not has_unlimited_files else 999,
            'has_unlimited_files': has_unlimited_files,
            'can_upload_files': can_upload_files,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        source = self.get_source()
        
        # 檢查檔案上傳限制
        limit, _ = Limit.objects.get_or_create(user=request.user)
        is_superuser = request.user.is_superuser
        has_unlimited_files = is_superuser
        
        # 獲取當前資料源的檔案數量（使用假資料數量）
        current_file_count = 5  # 假資料中有5個檔案
        
        uploaded_files = request.FILES.getlist('files')
        
        if not has_unlimited_files and current_file_count + len(uploaded_files) > limit.file_limit_per_source:
            remaining_slots = limit.file_limit_per_source - current_file_count
            messages.error(
                request, 
                f'檔案數量超過限制！此資料源最多可上傳 {limit.file_limit_per_source} 個檔案，'
                f'目前已有 {current_file_count} 個檔案，還可以上傳 {remaining_slots} 個檔案。'
            )
            return self.get(request, *args, **kwargs)
        
        # 處理檔案上傳（目前還是假處理，因為用戶要求檔案部分維持假資料）
        if uploaded_files:
            file_names = [file.name for file in uploaded_files]
            messages.success(request, f'成功上傳 {len(uploaded_files)} 個檔案：{", ".join(file_names)}')
            return redirect('source_detail', pk=source.id)
        else:
            messages.error(request, '請選擇要上傳的檔案。')
            return self.get(request, *args, **kwargs)
