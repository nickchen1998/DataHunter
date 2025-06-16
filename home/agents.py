import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate

# 導入文檔工廠
from home.documents import DocumentFactory
from symptoms.models import Symptom
from gov_datas.models import Dataset


class ChatAgent:
    """通用聊天代理，負責基於參考資料或自身知識回答問題"""
    
    def __init__(self):
        """初始化聊天代理"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
    
    def process_query(self, user_question: str, references: List[Dict[str, Any]]) -> str:
        """
        處理用戶查詢
        
        Args:
            user_question: 用戶問題
            references: 參考資料列表
            
        Returns:
            AI 回答字串
        """
        if references:
            return self._answer_with_references(user_question, references)
        else:
            return self._answer_without_references(user_question)

    def _answer_with_references(self, user_question: str, references: List[Dict[str, Any]]) -> str:
        """基於參考資料回答問題"""
        try:
            # 檢測參考資料類型並創建文檔
            documents = self._create_documents_from_references(references)
            
            if not documents:
                return self._answer_without_references(user_question)

            # 根據資料類型創建相應的提示模板
            data_type = self._detect_data_type(references)
            system_prompt = self._get_system_prompt(data_type)
            
            # 將所有文檔內容合併作為上下文
            context = "\n\n".join([doc.page_content for doc in documents])
            
            # 創建提示模板並直接執行
            prompt = ChatPromptTemplate.from_template(system_prompt)
            chain = prompt | self.llm
            
            # 執行查詢
            result = chain.invoke({
                "input": user_question,
                "context": context
            })
            
            response = result.content
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

    def _create_documents_from_references(self, references: List[Dict[str, Any]]) -> List[Document]:
        """從參考資料創建 Document 列表"""
        if not references:
            return []
        
        # 檢測資料類型
        data_type = self._detect_data_type(references)
        
        try:
            # 使用 DocumentFactory 創建文檔
            factory = DocumentFactory(references, data_type)
            return factory.get_documents()
        except Exception as e:
            print(f"創建文檔時發生錯誤：{e}")
            return []

    def _detect_data_type(self, references: List[Dict[str, Any]]) -> str:
        """檢測參考資料的類型"""
        if not references:
            return Symptom.__name__  # 預設類型
        
        # 檢查第一筆資料來判斷類型
        first_ref = references[0]
        
        # 症狀資料通常有這些欄位
        symptom_fields = {'department', 'gender', 'symptom', 'question', 'answer'}
        
        # 政府資料通常有這些欄位 (根據實際的 Dataset 模型)
        gov_data_fields = {'name', 'category', 'department', 'description', 'dataset_id', 'columns_description', 'license', 'price'}
        
        ref_keys = set(first_ref.keys())
        
        # 計算欄位匹配度
        symptom_match = len(symptom_fields.intersection(ref_keys))
        gov_data_match = len(gov_data_fields.intersection(ref_keys))
        
        # 特別檢查：如果有 dataset_id 或 category 且沒有 gender/symptom，很可能是政府資料
        if ('dataset_id' in ref_keys or 'category' in ref_keys) and 'gender' not in ref_keys and 'symptom' not in ref_keys:
            return Dataset.__name__
        
        # 特別檢查：如果有 gender 和 symptom，很可能是症狀資料
        if 'gender' in ref_keys and 'symptom' in ref_keys:
            return Symptom.__name__
        
        # 否則根據匹配度決定
        if gov_data_match > symptom_match:
            return Dataset.__name__
        else:
            return Symptom.__name__

    def _get_system_prompt(self, data_type: str) -> str:
        """根據資料類型獲取相應的系統提示"""
        if data_type == Symptom.__name__:
            return """你是一個專業的醫療資訊助手。請根據用戶提供的參考資料回答問題。

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
        
        elif data_type == Dataset.__name__:
            return """你是一個專業的資料分析助手。請根據用戶提供的政府開放資料集回答問題。

回答原則：
1. **優先使用參考資料**：主要基於用戶選擇的資料集資訊進行回答
2. **資料分析**：可以基於資料集的描述、欄位說明等進行分析和建議
3. **適度延伸**：如果參考資料相關但不完全匹配，可以進行適度的專業延伸
4. **明確來源**：清楚說明回答是基於用戶提供的參考資料
5. **實用建議**：提供如何使用這些資料集的建議

用戶提供的參考資料：
{context}

用戶問題：{input}

請基於以上參考資料詳細回答用戶問題。如果參考資料中沒有直接答案，請基於相關資料提供有用的建議和資訊。"""
        
        else:
            # 通用提示
            return """你是一個專業的資料分析助手。請根據用戶提供的參考資料回答問題。

回答原則：
1. **優先使用參考資料**：主要基於用戶選擇的參考資料進行回答
2. **靈活解釋**：可以基於參考資料進行合理的解釋、總結和建議
3. **適度延伸**：如果參考資料相關但不完全匹配，可以進行適度的專業延伸
4. **明確來源**：清楚說明回答是基於用戶提供的參考資料
5. **專業提醒**：提醒用戶資料僅供參考

用戶提供的參考資料：
{context}

用戶問題：{input}

請基於以上參考資料詳細回答用戶問題。"""

    def _get_data_type_name(self, data_type: str) -> str:
        """獲取資料類型的中文名稱"""
        type_names = {
            Symptom.__name__: "醫療症狀",
            Dataset.__name__: "政府開放資料"
        }
        return type_names.get(data_type, "")

    @classmethod
    def get_supported_data_types(cls) -> List[str]:
        """獲取支援的資料類型"""
        return DocumentFactory.get_supported_types() 