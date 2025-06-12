from rest_framework.serializers import ModelSerializer, CharField, IntegerField
from rest_framework import serializers
from symptoms.models import Symptom
import json


class SymptomSerializer(ModelSerializer):
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
    page = IntegerField(
        required=False, 
        min_value=1, 
        default=1,
        help_text="頁碼，從 1 開始",
        write_only=True
    )
    page_size = IntegerField(
        required=False, 
        min_value=1, 
        max_value=100, 
        default=10,
        help_text="每頁資料筆數，最大 100 筆",
        write_only=True
    )

    class Meta:
        model = Symptom
        fields = "__all__"
        extra_kwargs = {
            "question_embeddings": {"write_only": True},
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('context', {}).get('request')
        
        if 'data' in kwargs:
            data = kwargs['data']
            if isinstance(data, (bytes, str)):
                try:
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    kwargs['data'] = json.loads(data)
                except json.JSONDecodeError as e:
                    kwargs['data'] = {}
                    self._json_decode_error = f"JSON 格式錯誤：{str(e)}"
                except UnicodeDecodeError as e:
                    kwargs['data'] = {}
                    self._json_decode_error = f"編碼錯誤：{str(e)}"
        
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        if hasattr(self, '_json_decode_error'):
            raise serializers.ValidationError({
                'json_format': self._json_decode_error
            })
        
        if (self.request and 
            any(key in attrs for key in ['department', 'gender', 'question', 'page', 'page_size'])):
            
            if self.request.content_type != 'application/json':
                raise serializers.ValidationError({
                    'request_format': f'API 請求必須使用 application/json 格式，收到的格式：{self.request.content_type or "None"}'
                })
        
        return super().validate(attrs)

    def validate_department(self, value):
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

    def create_response(self, queryset, page_obj):
        return {
            'count': queryset.count(),
            'total_pages': page_obj.paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': SymptomSerializer(page_obj.object_list, many=True).data
        }
