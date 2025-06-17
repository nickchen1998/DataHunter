from symptoms.models import Symptom
from gov_datas.models import Dataset
from langchain.schema import Document
from typing import List, Dict, Any, Optional


class DocumentFactory:
    """文檔工廠類別，負責將不同類型的資料轉換為 LangChain Document"""

    def __init__(self, datas: List[Dict[str, Any]], data_type: str):
        """
        初始化文檔工廠
        
        Args:
            datas: 要轉換的資料列表
            data_type: 資料類型 (可以是 "Symptom", "Dataset", "Mixed" 或模型類名)
        """
        # 支援字串形式和模型類名形式的映射
        self.factory_mapping = {
            # 新的字串形式
            "Symptom": self.format_symptom_to_document,
            "Dataset": self.format_gov_data_to_document,
            "Mixed": self.format_mixed_to_document,
            # 舊的模型類名形式（向後兼容）
            Symptom.__name__: self.format_symptom_to_document,
            Dataset.__name__: self.format_gov_data_to_document
        }
        
        if data_type not in self.factory_mapping:
            raise ValueError(f"不支援的資料類型: {data_type}")
        
        self.factory = self.factory_mapping[data_type]
        self.datas = datas
        self.data_type = data_type
    
    def get_documents(self) -> List[Document]:
        """取得轉換後的 Document 列表"""
        if not self.datas:
            return []
        return self.factory(self.datas)

    def format_symptom_to_document(self, datas: List[Dict[str, Any]]) -> List[Document]:
        """將症狀資料轉換為 Document"""
        documents = []
        for data in datas:
            # 構建主要內容
            content_parts = []
            
            # 添加科別資訊
            if data.get("department"):
                content_parts.append(f"科別：{data.get('department')}")
            
            # 添加性別資訊
            if data.get("gender"):
                content_parts.append(f"性別：{data.get('gender')}")
            
            # 添加主訴
            if data.get("symptom"):
                content_parts.append(f"主訴：{data.get('symptom')}")
            
            # 添加問題描述
            if data.get("question"):
                content_parts.append(f"問題描述：{data.get('question')}")
            
            # 添加醫師回答 (作為主要內容)
            if data.get("answer"):
                content_parts.append(f"醫師回答：{data.get('answer')}")
            
            page_content = "\n".join(content_parts)
            
            document = Document(
                page_content=page_content,
                metadata={
                    "type": "symptom",
                    "id": data.get("id"),
                    "department": data.get("department"),
                    "gender": data.get("gender"),
                    "symptom": data.get("symptom"),
                    "question": data.get("question"),
                    "answer": data.get("answer")
                }
            )
            documents.append(document)
        
        return documents

    def format_gov_data_to_document(self, datasets: List[Dict[str, Any]]) -> List[Document]:
        """將政府資料轉換為 Document"""
        documents = []
        for data in datasets:
            # 構建主要內容
            content_parts = []
            
            # 添加資料集名稱
            if data.get("name"):
                content_parts.append(f"資料集名稱：{data.get('name')}")
            
            # 添加服務分類
            if data.get("category"):  # 模型中是 category 不是 service_category
                content_parts.append(f"服務分類：{data.get('category')}")
            
            # 添加資料提供機關
            if data.get("department"):  # 模型中是 department 不是 provider_agency
                content_parts.append(f"資料提供機關：{data.get('department')}")
            
            # 添加資料集描述
            if data.get("description"):
                content_parts.append(f"資料集描述：{data.get('description')}")
            
            # 添加主要欄位說明
            if data.get("columns_description"):  # 模型中是 columns_description
                # 如果是列表，轉換為字串
                if isinstance(data.get("columns_description"), list):
                    field_desc = "、".join(data.get("columns_description"))
                else:
                    field_desc = str(data.get("columns_description"))
                content_parts.append(f"主要欄位說明：{field_desc}")
            
            # 添加更新頻率
            if data.get("update_frequency"):
                content_parts.append(f"更新頻率：{data.get('update_frequency')}")
            
            # 添加授權方式
            if data.get("license"):
                content_parts.append(f"授權方式：{data.get('license')}")
            
            # 添加計費方式
            if data.get("price"):
                content_parts.append(f"計費方式：{data.get('price')}")
            
            page_content = "\n".join(content_parts)
            
            document = Document(
                page_content=page_content,
                metadata={
                    "type": "gov_data",
                    "id": data.get("dataset_id") or data.get("id"),
                    "name": data.get("name"),
                    "category": data.get("category"),  # 修正欄位名稱
                    "department": data.get("department"),  # 修正欄位名稱
                    "description": data.get("description"),
                    "columns_description": data.get("columns_description"),  # 修正欄位名稱
                    "update_frequency": data.get("update_frequency"),
                    "license": data.get("license"),
                    "price": data.get("price"),
                    "url": data.get("url"),
                    "contact_person": data.get("contact_person"),
                    "contact_phone": data.get("contact_phone")
                }
            )
            documents.append(document)
        
        return documents

    @classmethod
    def create_from_model_name(cls, datas: List[Dict[str, Any]], model_name: str) -> 'DocumentFactory':
        """從模型名稱創建工廠實例"""
        return cls(datas, model_name)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """取得支援的資料類型列表"""
        return ["Mixed", Symptom.__name__, Dataset.__name__]
    