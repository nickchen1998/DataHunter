from typing import Dict, List, Optional, Any
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from utils.search import hybrid_search_with_rerank

from symptoms.models import Symptom
from symptoms.utils import build_symptom_queryset


class SymptomQueryInput(BaseModel):
    """症狀查詢工具的輸入參數"""
    reference_id_list: List[int] = Field(default=[], description="參考資料ID列表")
    department: str = Field(default="", description="科別")
    gender: str = Field(default="", description="性別")
    question: str = Field(default="", description="症狀關鍵字")


class SymptomDataRetrievalTool(BaseTool):
    """症狀資料檢索工具 - 純粹的資料檢索功能"""
    
    name: str = "symptom_data_retrieval"
    description: str = """檢索症狀資料的工具。

使用情境：
- 若有參考資料ID (reference_id_list)，請直接使用這些 ID 進行查詢。
- 若無參考資料，請根據用戶提供的內容自動分析適合的科別 (department)、性別 (gender) 與問題 (question) 後進行查詢。

參數描述：
- gender 除了支援的性別之外，也可以填寫空字串，表示不限制性別
- department 除了支援的科別之外，也可以填寫空字串，表示不限制科別
"""
   
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
        reference_id_list: List[int] = [],
        department: str = "",
        gender: str = "",
        question: str = "",
    ) -> str:
        
        if reference_id_list:
            queryset = Symptom.objects.filter(id__in=reference_id_list)
            queryset = hybrid_search_with_rerank(
                queryset=queryset, 
                vector_field_name="question_embeddings",
                text_field_name="question",
                original_question=question
            )
        else:
            queryset = build_symptom_queryset(department, gender, question)
        
        if not queryset:
            return "沒有找到符合條件的症狀資料。"


        result = f"找到 {queryset.count()} 筆症狀資料：\n\n"

        for i, symptom in enumerate(queryset, 1):
            result += f"{i}. 【{symptom.department}】{symptom.gender}\n"
            result += f"   主訴：{symptom.symptom}\n"
            result += f"   問題：{symptom.question[:100]}{'...' if len(symptom.question) > 100 else ''}\n"
            result += f"   回答：{symptom.answer[:100]}{'...' if len(symptom.answer) > 100 else ''}\n\n"
        
        symptom_prompt = self._get_symptom_prompt()
        prompt = ChatPromptTemplate.from_template(symptom_prompt)
        chain = prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        result = chain.invoke({"context": result, "input": question})
        return result.content
    
    @staticmethod
    def _get_symptom_prompt() -> str:
        prompt = """
        你是一個專業的醫療資訊助手。請根據用戶提供的參考資料回答問題。

回答原則：
1. **優先使用參考資料**：主要基於用戶選擇的參考資料進行回答
2. **靈活解釋**：可以基於參考資料進行合理的解釋、總結和建議
3. **適度延伸**：如果參考資料相關但不完全匹配，可以進行適度的專業延伸
4. **明確來源**：清楚說明回答是基於用戶提供的參考資料
5. **專業提醒**：始終提醒這些資料僅供參考，具體診斷需諮詢專業醫師

用戶提供的參考資料：
{context}

用戶問題：{input}

請基於以上參考資料詳細回答用戶問題。如果參考資料中沒有直接答案，請基於相關資料提供有用的建議和資訊。"""
        return prompt
    