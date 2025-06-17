import json
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from utils.search import hybrid_search_with_rerank

from symptoms.models import Symptom
from symptoms.utils import build_symptom_queryset


class SymptomQueryInput(BaseModel):
    """症狀查詢工具的輸入參數"""
    reference_id_list: str = Field(default="", description="參考資料ID列表，請以 json 格式傳遞，例如：[1, 2, 3]")
    department: str = Field(default="", description="科別")
    gender: str = Field(default="", description="性別")
    question: str = Field(default="", description="使用者原本的問題（不包含參考資料ID）")


class SymptomDataRetrievalTool(BaseTool):
    """症狀資料檢索工具 - 純粹的資料檢索功能"""
    
    name: str = "symptom_data_retrieval"
   
    def __init__(self):
        supported_departments = Symptom.objects.values_list("department", flat=True).distinct()
        supported_genders = Symptom.objects.values_list("gender", flat=True).distinct()

        description = """檢索症狀資料的工具。

使用情境：
- 若有參考資料ID (reference_id_list)，請直接使用這些 ID 進行查詢。
- 若無參考資料，請根據用戶提供的內容自動分析適合的科別 (department)、性別 (gender) 與問題 (question) 後進行查詢。

參數描述：
- gender 除了支援的性別之外，也可以填寫空字串，表示不限制性別
- department 除了支援的科別之外，也可以填寫空字串，表示不限制科別
"""

        description += f"\n\n支援的科別：{list(supported_departments)}\n支援的性別：{list(supported_genders)}"

        super().__init__(
            name="symptom_data_retrieval",
            description=description,
            args_schema=SymptomQueryInput,
        )
    
    def _run(
        self, 
        reference_id_list: str = "",
        department: str = "",
        gender: str = "",
        question: str = "",
    ) -> str:
        
        if reference_id_list:
            try:
                reference_id_list = json.loads(reference_id_list)
                queryset = Symptom.objects.filter(id__in=reference_id_list)
                # 只有當有參考資料且需要重新排序時才使用 hybrid_search_with_rerank
                if question and question != "一般症狀諮詢":
                    queryset = hybrid_search_with_rerank(
                        queryset=queryset, 
                        vector_field_name="question_embeddings",
                        text_field_name="question",
                        original_question=question
                    )
            except (json.JSONDecodeError, ValueError):
                return "參考資料ID格式錯誤，請提供正確的JSON格式。"
        else:
            queryset = build_symptom_queryset(department, gender, question)
        

        result = f"找到 {queryset.count()} 筆類似症狀資料：\n\n"

        for i, symptom in enumerate(queryset, 1):
            result += f"{i}. 【{symptom.department}】{symptom.gender}\n"
            result += f"   主訴：{symptom.symptom}\n"
            result += f"   問題：{symptom.question}\n"
            result += f"   回答：{symptom.answer}\n\n"
        
        return result, list(queryset.values_list("id", flat=True))
    