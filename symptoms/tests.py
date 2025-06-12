from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from symptoms.models import Symptom
from datetime import datetime
import json


class SymptomModelTest(TestCase):
    """測試 Symptom 模型"""
    
    def setUp(self):
        self.symptom = Symptom.objects.create(
            subject_id=123,
            department='家醫科',
            symptom='發燒',
            question='醫生您好，我最近一直有發燒的狀況',
            answer='您好，建議您多喝水、多休息',
            gender='男',
            question_time=datetime.now(),
            answer_time=datetime.now(),
            question_embeddings=[0.1] * 1536  # 模擬向量
        )
    
    def test_symptom_creation(self):
        """測試症狀資料建立"""
        self.assertEqual(self.symptom.subject_id, 123)
        self.assertEqual(self.symptom.department, '家醫科')
        self.assertEqual(self.symptom.gender, '男')
        self.assertIsNotNone(self.symptom.created_at)


class SymptomAPITest(APITestCase):
    """測試 Symptom API"""
    
    def setUp(self):
        """建立測試資料"""
        self.api_url = reverse('symptom_api_search')
        
        # 建立測試資料
        for i in range(15):
            Symptom.objects.create(
                subject_id=100 + i,
                department='家醫科' if i % 2 == 0 else '皮膚科',
                symptom=f'症狀{i}',
                question=f'問題{i}：這是測試問題',
                answer=f'回答{i}：這是測試回答',
                gender='男' if i % 2 == 0 else '女',
                question_time=datetime.now(),
                answer_time=datetime.now(),
                question_embeddings=[0.1] * 1536
            )
    
    def test_api_basic_search(self):
        """測試基本搜尋功能"""
        data = {
            'department': '',
            'gender': '',
            'question': '',
            'page': 1,
            'page_size': 5
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 檢查分頁資訊
        self.assertIn('count', response_data)
        self.assertIn('results', response_data)
        self.assertEqual(len(response_data['results']), 5)
        self.assertEqual(response_data['count'], 15)
    
    def test_api_department_filter(self):
        """測試部門篩選功能"""
        data = {
            'department': '家醫科',
            'gender': '',
            'question': '',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 檢查篩選結果
        self.assertEqual(response_data['count'], 8)  # 15個中有8個是家醫科
        for result in response_data['results']:
            self.assertEqual(result['department'], '家醫科')
    
    def test_api_gender_filter(self):
        """測試性別篩選功能"""
        data = {
            'department': '',
            'gender': '女',
            'question': '',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 檢查篩選結果
        self.assertEqual(response_data['count'], 7)  # 15個中有7個是女性
        for result in response_data['results']:
            self.assertEqual(result['gender'], '女')
    
    def test_api_pagination(self):
        """測試分頁功能"""
        # 測試第一頁
        data = {
            'department': '',
            'gender': '',
            'question': '',
            'page': 1,
            'page_size': 5
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['results']), 5)
        
        # 測試第二頁
        data['page'] = 2
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['results']), 5)
    
    def test_api_invalid_pagination(self):
        """測試無效的分頁參數"""
        data = {
            'department': '',
            'gender': '',
            'question': '',
            'page': -1,  # 無效的頁碼
            'page_size': 200  # 超過最大限制
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('details', response_data)
    
    def test_api_invalid_department(self):
        """測試無效的部門"""
        data = {
            'department': '不存在的部門',
            'gender': '',
            'question': '',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('department', response_data['details'])
    
    def test_api_invalid_gender(self):
        """測試無效的性別"""
        data = {
            'department': '',
            'gender': '不存在的性別',
            'question': '',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('gender', response_data['details'])
    
    def test_api_invalid_content_type(self):
        """測試無效的 Content-Type"""
        data = {
            'department': '家醫科',
            'gender': '',
            'question': '',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post(
            self.api_url,
            data=data,  # 不使用 JSON 格式
            content_type='application/x-www-form-urlencoded'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('request_format', response_data['details'])
    
    def test_api_invalid_json(self):
        """測試無效的 JSON 格式"""
        response = self.client.post(
            self.api_url,
            data='{"invalid": json}',  # 無效的 JSON
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('json_format', response_data['details'])
    
    def test_api_question_search(self):
        """測試問題搜尋功能"""
        data = {
            'department': '',
            'gender': '',
            'question': '測試',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 所有結果都應該包含"測試"關鍵字
        for result in response_data['results']:
            self.assertIn('測試', result['question'])
    
    def test_api_combined_filters(self):
        """測試組合篩選功能"""
        data = {
            'department': '家醫科',
            'gender': '男',
            'question': '',
            'page': 1,
            'page_size': 10
        }
        
        response = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 檢查組合篩選結果
        for result in response_data['results']:
            self.assertEqual(result['department'], '家醫科')
            self.assertEqual(result['gender'], '男')


class SymptomWebViewTest(TestCase):
    """測試 Symptom 網頁視圖"""
    
    def setUp(self):
        self.url = reverse('symptom_list')
        
        # 建立測試資料
        Symptom.objects.create(
            subject_id=123,
            department='家醫科',
            symptom='發燒',
            question='測試問題',
            answer='測試回答',
            gender='男',
            question_time=datetime.now(),
            answer_time=datetime.now(),
            question_embeddings=[0.1] * 1536
        )
    
    def test_symptom_list_view(self):
        """測試症狀列表頁面"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '衛生福利部 - 台灣 e 院')
        self.assertContains(response, '家醫科')
    
    def test_symptom_list_with_filters(self):
        """測試帶篩選條件的症狀列表頁面"""
        response = self.client.get(self.url, {
            'department': '家醫科',
            'gender': '男',
            'question': '測試'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '家醫科')
        self.assertContains(response, '男')


class BaseSerializerTest(TestCase):
    """測試 BaseSerializer 功能"""
    
    def test_pagination_parameters(self):
        """測試分頁參數定義"""
        from DataHunter.serializers import BaseSerializer
        
        # 測試欄位存在
        data = {'page': 1, 'page_size': 10}
        serializer = BaseSerializer(data=data)
        
        self.assertIn('page', serializer.fields)
        self.assertIn('page_size', serializer.fields)
        
        # 檢查欄位屬性
        page_field = serializer.fields['page']
        page_size_field = serializer.fields['page_size']
        
        self.assertTrue(page_field.write_only)
        self.assertTrue(page_size_field.write_only)
        self.assertEqual(page_field.default, 1)
        self.assertEqual(page_size_field.default, 10)
    
    def test_json_parsing_functionality(self):
        """測試 JSON 解析功能"""
        from DataHunter.serializers import BaseSerializer
        
        # 測試 bytes 格式
        json_bytes = json.dumps({'page': 1, 'page_size': 10}).encode('utf-8')
        serializer = BaseSerializer(data=json_bytes)
        self.assertIsInstance(serializer.initial_data, dict)
        
        # 測試 string 格式
        json_string = json.dumps({'page': 2, 'page_size': 20})
        serializer = BaseSerializer(data=json_string)
        self.assertIsInstance(serializer.initial_data, dict)


class BasePaginationTest(TestCase):
    """測試 BasePagination 功能"""
    
    def test_pagination_attributes(self):
        """測試分頁器屬性"""
        from DataHunter.paginator import BasePagination
        
        paginator = BasePagination()
        
        # 檢查基本屬性
        self.assertEqual(paginator.page_size, 10)
        self.assertEqual(paginator.max_page_size, 100)
        self.assertEqual(paginator.page_size_query_param, 'page_size')


class SymptomSerializerTest(TestCase):
    """測試 SymptomSerializer 功能"""
    
    def test_serializer_fields(self):
        """測試 serializer 欄位定義"""
        from symptoms.serializers import SymptomSerializer
        
        serializer = SymptomSerializer()
        
        # 檢查搜尋欄位
        self.assertIn('department', serializer.fields)
        self.assertIn('gender', serializer.fields)
        self.assertIn('question', serializer.fields)
        
        # 檢查分頁欄位
        self.assertIn('page', serializer.fields)
        self.assertIn('page_size', serializer.fields)
        
        # 檢查搜尋欄位設定
        self.assertEqual(serializer.search_fields, ['department', 'gender', 'question'])
    
    def test_json_parsing(self):
        """測試 JSON 解析功能"""
        from symptoms.serializers import SymptomSerializer
        
        json_data = json.dumps({
            'department': '家醫科',
            'gender': '男',
            'question': '發燒',
            'page': 1,
            'page_size': 10
        })
        
        serializer = SymptomSerializer(data=json_data)
        self.assertIsInstance(serializer.initial_data, dict)
        self.assertEqual(serializer.initial_data['department'], '家醫科')
    
    def test_invalid_json_parsing(self):
        """測試無效 JSON 解析"""
        from symptoms.serializers import SymptomSerializer
        
        invalid_json = '{"invalid": json}'
        serializer = SymptomSerializer(data=invalid_json)
        
        # 檢查是否有 JSON 錯誤標記
        self.assertTrue(hasattr(serializer, '_json_decode_error'))


class UtilsFunctionTest(TestCase):
    """測試工具函數"""
    
    def test_build_symptom_queryset_function(self):
        """測試 build_symptom_queryset 函數"""
        from symptoms.utils import build_symptom_queryset
        
        # 建立測試資料
        Symptom.objects.create(
            subject_id=123,
            department='家醫科',
            symptom='發燒',
            question='測試問題',
            answer='測試回答',
            gender='男',
            question_time=datetime.now(),
            answer_time=datetime.now(),
            question_embeddings=[0.1] * 1536
        )
        
        # 測試無參數調用
        result = build_symptom_queryset(None, None, None)
        self.assertIsNotNone(result)
        self.assertEqual(result.count(), 1)
        
        # 測試有參數調用
        result = build_symptom_queryset('家醫科', '男', '測試')
        self.assertIsNotNone(result)
        self.assertEqual(result.count(), 1)
        
        # 測試不匹配的參數
        result = build_symptom_queryset('皮膚科', '女', '不存在')
        self.assertEqual(result.count(), 0)
