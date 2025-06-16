from typing import Dict, List, Optional, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json

from symptoms.models import Symptom
from symptoms.utils import build_symptom_queryset


class SymptomQueryInput(BaseModel):
    """症狀查詢工具的輸入參數"""
    department: str = Field(default="", description="科別")
    gender: str = Field(default="", description="性別")
    question: str = Field(default="", description="症狀關鍵字")
    limit: int = Field(default=10, description="返回結果數量限制")


class SymptomDataRetrievalTool(BaseTool):
    """症狀資料檢索工具 - 純粹的資料檢索功能"""
    
    name: str = "symptom_data_retrieval"
    description: str = """
    檢索症狀資料的工具。
    
    輸入參數：
    - department: 科別 (可選)
    - gender: 性別 (可選) 
    - question: 症狀關鍵字 (可選)
    - limit: 返回結果數量限制 (預設10)
    """
    
    def _run(
        self, 
        department: str = None, 
        gender: str = None, 
        question: str = None, 
        limit: int = 10
    ) -> str:
        """檢索症狀資料"""
        
        try:
            queryset = build_symptom_queryset(department, gender, question)
            symptoms = list(queryset[:limit])
            
            if not symptoms:
                return "沒有找到符合條件的症狀資料。"
            
            result = f"找到 {len(symptoms)} 筆症狀資料：\n\n"
            
            for i, symptom in enumerate(symptoms, 1):
                result += f"{i}. 【{symptom.department}】{symptom.gender}\n"
                result += f"   主訴：{symptom.symptom}\n"
                result += f"   問題：{symptom.question[:100]}{'...' if len(symptom.question) > 100 else ''}\n"
                result += f"   回答：{symptom.answer[:100]}{'...' if len(symptom.answer) > 100 else ''}\n\n"
            
            return result
            
        except Exception as e:
            return f"檢索資料時發生錯誤：{str(e)}"

    def get_symptom_data(
        self, 
        department: str = None, 
        gender: str = None, 
        question: str = None, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """獲取症狀資料，返回字典列表格式"""
        
        try:
            queryset = build_symptom_queryset(department, gender, question)
            symptoms = list(queryset[:limit])
            
            result = []
            for symptom in symptoms:
                result.append({
                    'id': symptom.id,
                    'department': symptom.department,
                    'gender': symptom.gender,
                    'symptom': symptom.symptom,
                    'question': symptom.question,
                    'answer': symptom.answer
                })
            
            return result
            
        except Exception as e:
            return [] 