import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate

# 導入文檔工廠
from home.documents import DocumentFactory
from symptoms.models import Symptom
from gov_datas.models import Dataset
from symptoms.tools import SymptomDataRetrievalTool


class ChatAgent:
    """通用聊天代理，負責基於參考資料或自身知識回答問題"""
    
    def __init__(self):
        """初始化聊天代理"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
    
    def process_query(self, user_question: str, reference_id_list: List[int], data_type: str = "Mixed") -> str:
        """處理用戶查詢
        
        Args:
            user_question: 用戶問題
            reference_id_list: 參考資料ID列表
            data_type: 資料源類型，由前台傳入，可能的值：'Symptom', 'Dataset', 'Mixed'
                      當為 'Mixed' 時，忽略參考資料，當作沒有參考資料處理
        """

        if reference_id_list:
            return self._answer_with_references(user_question, reference_id_list, data_type)
        
        return self._answer_without_references(user_question)

    def _answer_with_references(self, user_question: str, reference_id_list: List[int], data_type: str = "Mixed") -> str:
        """基於參考資料回答問題
        
        Args:
            user_question: 用戶問題
            reference_id_list: 參考資料ID列表
            data_type: 資料源類型，由前台傳入
        """
        try:
            response = ""
            if data_type == Symptom.__name__:
                response = SymptomDataRetrievalTool().invoke({
                    "reference_id_list": reference_id_list,
                    "question": user_question
                })
            
            response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，實際應用時請諮詢相關專業人士。"
            
            return response
            
        except Exception as e:
            return f"處理參考資料時發生錯誤：{str(e)}。請檢查您的參考資料是否正確。"

    def _answer_without_references(self, user_question: str) -> str:
        """無參考資料時的回答"""
        try:
            system_prompt = """你是一個專業的資料分析助手。用戶沒有提供任何參考資料。

回答原則：
1. **明確說明**：請務必告訴使用者他沒有選擇參考資料，所以資訊可能會不正確。
2. **專業回答**：基於你的知識提供專業、準確的資訊
3. **建議參考資料**：建議用戶選擇相關的參考資料以獲得更準確的資訊
4. **保持謹慎**：對於可能涉及專業建議的問題，提醒用戶諮詢專業人士

請回答用戶的問題：{input}"""

            prompt = ChatPromptTemplate.from_template(system_prompt)
            chain = prompt | self.llm
            
            result = chain.invoke({"input": user_question})
            
            return result.content
            
        except Exception as e:
            return f"處理問題時發生錯誤：{str(e)}"

   