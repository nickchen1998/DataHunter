import json
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from utils.search import hybrid_search_with_rerank

from gov_datas.models import Dataset, File, ASSOCIATED_CATEGORIES_DATABASE_NAME


class GovDataDatasetQueryInput(BaseModel):
    """Dataset 查詢工具的輸入參數"""
    question: str = Field(description="使用者原本的問題")
    reference_id_list: str = Field(default="", description="參考資料 ID，以 JSON 字串格式傳入，例如：[1, 2, 3]")
    category: str = Field(default="", description="服務分類篩選")


class GovDataDatasetQueryTool(BaseTool):
    """Dataset 查詢工具 - 檢索資料集及其相關檔案資訊"""
    
    name: str = "gov_data_dataset_retrieval"
   
    def __init__(self):
        description = """檢索政府開放資料集及其相關檔案的工具。

使用情境：
- 若有資料集參考ID (reference_id_list)，請將其轉換為 JSON 字串格式傳入，例如：[1, 2, 3]，並將使用者原本的問題擷取後傳入。
- 若無參考資料集，請根據使用者提供的內容自動分析適合的服務分類 (category) 與問題 (question) 後進行查詢。

此工具會返回：
- 資料集的基本資訊（名稱、類別、描述等）
- 相關檔案的詳細資訊（格式、資料表名稱、資料庫名稱等）
- **完整欄位對應 (JSON格式)**：可直接用於 custom_nl2sql_query 工具的 column_name_mapping_list 參數

參數描述：
- question: 使用者的查詢問題，用於語意搜尋
- reference_id_list: 指定要查詢的資料集ID列表，JSON字串格式
- category: 服務分類篩選，可以填寫空字串表示不限制分類"""

        supported_categories = list(ASSOCIATED_CATEGORIES_DATABASE_NAME.keys())
        description += f"\n\n支援的服務分類：{supported_categories}"

        super().__init__(
            name="gov_data_dataset_retrieval",
            description=description,
            args_schema=GovDataDatasetQueryInput,
        )
    
    def _run(
        self, 
        question: str,
        reference_id_list: str = "",
        category: str = "",
    ) -> str:
        
        if reference_id_list:
            try:
                reference_ids = json.loads(reference_id_list)
            except (json.JSONDecodeError, ValueError):
                return "參考資料ID格式錯誤，請提供正確的JSON格式。"
            
            # 使用指定的資料集ID進行查詢
            queryset = Dataset.objects.filter(id__in=reference_ids)
            if question.strip():
                # 如果有問題，使用語意搜尋重新排序
                queryset = hybrid_search_with_rerank(
                    queryset=queryset, 
                    vector_field_name="description_embeddings",
                    text_field_name="description",
                    original_question=question
                )
        else:
            # 建立基本查詢集
            queryset = Dataset.objects.all()
            
            # 根據分類篩選
            if category.strip():
                queryset = queryset.filter(category=category)
            
            # 使用語意搜尋
            if question.strip():
                queryset = hybrid_search_with_rerank(
                    queryset=queryset,
                    vector_field_name="description_embeddings", 
                    text_field_name="description",
                    original_question=question
                )

        result = f"找到 {queryset.count()} 筆相關資料集：\n\n"

        dataset_ids = []
        for i, dataset in enumerate(queryset, 1):
            dataset_ids.append(dataset.id)
            result += f"{i}. 【{dataset.category}】{dataset.name}\n"
            result += f"   資料集識別碼：{dataset.dataset_id}\n"
            result += f"   提供機關：{dataset.department}\n"
            result += f"   更新頻率：{dataset.update_frequency}\n"
            result += f"   授權方式：{dataset.license}\n"
            if dataset.description:
                result += f"   描述：{dataset.description[:200]}{'...' if len(dataset.description) > 200 else ''}\n"
            result += f"   網址：{dataset.url}\n"
            
            # 獲取該資料集的所有檔案
            files = File.objects.filter(dataset=dataset)
            if files.exists():
                result += f"   相關檔案 ({files.count()} 個)：\n"
                for j, file in enumerate(files, 1):
                    result += f"        資料表名稱：{file.table_name}\n"
                    result += f"        資料庫：{file.database_name}\n"
                    result += f"        編碼格式：{file.encoding}\n"
                        
                    # 將完整的欄位對應列表轉換為 JSON 字串
                    column_mapping_json = json.dumps(file.column_mapping_list, ensure_ascii=False)
                    result += f"        完整欄位對應 (JSON格式)：{column_mapping_json}\n"
                        
            else:
                result += "   相關檔案：無\n"
            
            result += "\n"
        
        return result, sorted(dataset_ids)
    