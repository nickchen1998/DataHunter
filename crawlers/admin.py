from django.contrib import admin
from .models import Dataset, File, Symptom


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('dataset_id', 'name', 'category', 'department', 'update_frequency', 'upload_time')
    list_filter = ('category', 'department', 'update_frequency', 'license')
    search_fields = ('name', 'description', 'department')
    readonly_fields = ('dataset_id', 'description_embeddings')
    ordering = ('-dataset_id',)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'table_name', 'original_format', 'database_name', 'created_at')
    list_filter = ('original_format', 'database_name', 'created_at')
    search_fields = ('table_name', 'dataset__name')
    readonly_fields = ('content_md5', 'created_at')
    ordering = ('-created_at',)


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('id', 'department', 'gender', 'symptom', 'question_time', 'answer_time')
    list_filter = ('department', 'gender', 'question_time')
    search_fields = ('symptom', 'question', 'answer', 'department')
    readonly_fields = ('question_embeddings',)
    ordering = ('-question_time',)
