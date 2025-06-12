from rest_framework.serializers import CharField
from rest_framework import serializers
from symptoms.models import Symptom
from DataHunter.serializers import BaseSerializer


class SymptomSerializer(BaseSerializer):
    """
    症狀資料的 Serializer，繼承 BaseSerializer 獲得分頁和 JSON 解析功能
    """
    # 搜尋參數
    department = CharField(
        required=False, 
        allow_blank=True, 
        max_length=255,
        help_text="篩選特定科別，例如：家醫科、皮膚科",
        write_only=True
    )
    gender = CharField(
        required=False, 
        allow_blank=True, 
        max_length=10,
        help_text="篩選性別，例如：男、女",
        write_only=True
    )
    question = CharField(
        required=False, 
        allow_blank=True,
        help_text="搜尋問題關鍵字，支援語意搜尋",
        write_only=True
    )
    
    # 定義搜尋欄位，用於 BaseSerializer 的 Content-Type 檢查
    search_fields = ['department', 'gender', 'question']

    class Meta:
        model = Symptom
        fields = ['id', 'subject_id', 'department', 'symptom', 'question', 'answer', 'gender', 'question_time', 'answer_time', 'created_at', 'page', 'page_size']
        read_only_fields = ['id', 'subject_id', 'symptom', 'answer', 'question_time', 'answer_time', 'created_at']

    def validate_department(self, value):
        """驗證部門是否存在"""
        if not value:
            return value
            
        available_departments = list(
            Symptom.objects.values_list('department', flat=True)
            .distinct()
            .order_by('department')
        )
        
        matching_departments = [dept for dept in available_departments if value.lower() in dept.lower()]
        
        if not matching_departments:
            raise serializers.ValidationError(
                f"部門 '{value}' 不存在。可用的部門選項：{', '.join(available_departments)}"
            )
        
        return value

    def validate_gender(self, value):
        """驗證性別是否有效"""
        if not value:
            return value
            
        available_genders = list(
            Symptom.objects.values_list('gender', flat=True)
            .distinct()
            .order_by('gender')
        )
        
        if value not in available_genders:
            raise serializers.ValidationError(
                f"性別 '{value}' 不支援。可用的性別選項：{', '.join(available_genders)}"
            )
        
        return value
