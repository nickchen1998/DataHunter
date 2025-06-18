import json
from langchain_core.tools import BaseTool, ToolException
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
from typing import Optional, List, Dict, Type
from pydantic import BaseModel, Field
from django.conf import settings
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent


class NL2SQLQueryInput(BaseModel):
    question: str = Field(description="使用者原本的問題")
    db_name: str = Field(default="", description="資料庫名稱")
    table_name: str = Field(default="", description="資料表名稱")
    column_name_mapping_list: str = Field(default="", description="欄位對應列表，JSON 格式，例如：[[\"a\", \"欄位描述\"], [\"b\", \"欄位描述\"]......]")


class CustomNL2SQLQueryTool(BaseTool):
    name: str = "custom_nl2sql_query"
    description: str = """根據自然語言問題，查詢指定資料表的 SQL 工具。

使用方法：
1. 先使用其他工具獲取要查詢的資訊
2. 從返回結果中提取：db_name（資料庫名稱）、table_name（資料表名稱）、完整欄位對應 (JSON格式)
3. 將完整欄位對應的 JSON 字串直接傳入 column_name_mapping_list 參數
4. 一次只能查詢一張資料表

注意：column_name_mapping_list 參數需要是有效的 JSON 字串格式，例如：[["a", "欄位描述"], ["b", "欄位描述"]]"""
    args_schema: Type[BaseModel] = NL2SQLQueryInput        

    def _run(
        self,
        question: str,
        db_name: str,
        table_name: str,
        column_name_mapping_list: str = None,
    ):
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        db_uri = f"postgresql://{settings.DATABASES['default']['USER']}:{settings.DATABASES['default']['PASSWORD']}@{settings.DATABASES['default']['HOST']}:{settings.DATABASES['default']['PORT']}/{db_name}"
        toolkit = SQLDatabaseToolkit(
            db=SQLDatabase.from_uri(db_uri, include_tables=[table_name]), 
            llm=llm
        )
        
        # 建立 prompt context
        additional_prompt = f"你只能查詢資料表 `{table_name}`。"
        if column_name_mapping_list:
            try:
                # 嘗試解析 JSON 格式的欄位對應列表
                mappings = json.loads(column_name_mapping_list)
                additional_prompt += "\n以下是欄位對應說明：\n"
                for mapping in mappings:
                    if isinstance(mapping, list) and len(mapping) >= 2:
                        col = mapping[0]
                        desc = mapping[1]
                        additional_prompt += f"- `{col}`：{desc}\n"
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                # 如果 JSON 解析失敗，記錄錯誤並繼續執行
                print(f"警告：無法解析欄位對應列表：{column_name_mapping_list}，錯誤：{e}")
                additional_prompt += f"\n注意：欄位對應資訊格式錯誤，請直接查詢資料表 `{table_name}`。"

        agent_executor = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True,
            handle_parsing_errors=True,
        )

        # 將額外的 prompt 信息與問題結合
        enhanced_question = f"{additional_prompt}\n\n用戶問題：{question}"
        
        try:
            result = agent_executor.run(enhanced_question)
            return f"查詢結果：{result}"
        except Exception as e:
            return f"查詢過程中發生錯誤：{str(e)}"
    