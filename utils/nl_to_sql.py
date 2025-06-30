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
    table_info_list: str = Field(default="", description="""資料表資訊列表，格式如下：
[
    {
        "database_name": "資料庫名稱",
        "table_name": "資料表名稱",
        "column_name_mapping_list": [[\"a\", \"欄位描述\"], [\"b\", \"欄位描述\"]] (不一定會有，若無則表示資料表無欄位對應說明，可直接使用欄位名稱查詢)
    },
    ...
]
""")


class CustomNL2SQLQueryTool(BaseTool):
    name: str = "custom_nl2sql_query"
    description: str = """根據自然語言問題，查詢指定資料表的 SQL 工具。

使用方法：
1. 先使用其他工具獲取要查詢的資訊
2. 使用 table_info_list 參數傳入所有可用資料表資訊，工具會自動篩選出指定資料庫中的資料表
3. 查詢的時候，如果是跟關鍵字有關的，可以使用模糊查詢的方式來查詢包含指定關鍵字的資料
4. 如果使用者的問題，沒有明確的指定說要查詢到什麼樣的資料，可以試著擷取該資料表當中的前 5 筆資料，並且將其資料內容作為回答的素材

table_info_list 格式：
[
    {
        "database_name": "資料庫名稱",
        "table_name": "資料表名稱",
        "column_name_mapping_list": [[\"a\", \"欄位描述\"], [\"b\", \"欄位描述\"]] (不一定會有，若無則表示資料表無欄位對應說明，可直接使用欄位名稱查詢)
    },
    ...
]"""
    args_schema: Type[BaseModel] = NL2SQLQueryInput        

    def _run(
        self,
        question: str,
        table_info_list: str,
    ):
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        
        # 解析 table_info_list 並按照 database_name 彙整
        table_info_list = json.loads(table_info_list)
        
        # 按照 database_name 分組
        db_tables = {}
        for table_info in table_info_list:
            database_name = table_info.get("database_name")
            if database_name not in db_tables:
                db_tables[database_name] = []
            db_tables[database_name].append({
                "table_name": table_info.get("table_name"),
                "column_name_mapping_list": table_info.get("column_name_mapping_list")
            })
        
        all_results = []
        
        for db_name, tables in db_tables.items():
            db_uri = f"postgresql://{settings.DATABASES['default']['USER']}:{settings.DATABASES['default']['PASSWORD']}@{settings.DATABASES['default']['HOST']}:{settings.DATABASES['default']['PORT']}/{db_name}"
            
            # 將資料表分批處理，每批最多2個資料表
            batch_size = 2
            for i in range(0, len(tables), batch_size):
                batch_tables = tables[i:i + batch_size]
                
                print(f"處理資料庫 {db_name} 的第 {i//batch_size + 1} 批資料表: {[t.get('table_name') for t in batch_tables]}")
                
                # 為此批次建立提示
                additional_prompt = f"你可以查詢資料庫 `{db_name}` 中的以下資料表：\n"
                
                for table_info in batch_tables:
                    table_name = table_info.get("table_name")
                    column_name_mapping_list = table_info.get("column_name_mapping_list")
                    
                    if table_name and column_name_mapping_list:
                        additional_prompt += f"\n資料表 `{table_name}` 的欄位對應說明：\n"
                        for column_name, column_description in column_name_mapping_list:
                            additional_prompt += f"- `{column_name}`：{column_description}\n"
                    else:
                        if table_name:
                            additional_prompt += f"\n資料表 `{table_name}` 無欄位對應說明，可直接查詢。\n"
                
                # 建立 SQLDatabaseToolkit，只包含這批次的資料表
                batch_table_names = [table["table_name"] for table in batch_tables if table.get("table_name")]
                toolkit = SQLDatabaseToolkit(
                    db=SQLDatabase.from_uri(db_uri, include_tables=batch_table_names), 
                    llm=llm
                )

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
                    if result and "I don't know" not in result:
                        all_results.append({
                            "database": db_name,
                            "tables": batch_table_names,
                            "result": result
                        })
                        print(f"成功查詢批次，獲得結果")
                    else:
                        print(f"此批次查詢無相關結果")
                except Exception as e:
                    print(f"批次查詢錯誤：{str(e)}")
                    continue
        
        # 組合所有查詢結果
        if not all_results:
            return "在所有可用資料表中都沒有找到相關資訊。"
        
        combined_result = "查詢結果摘要：\n\n"
        for idx, result_info in enumerate(all_results, 1):
            combined_result += f"=== 結果 {idx} ===\n"
            combined_result += f"資料庫：{result_info['database']}\n"
            combined_result += f"資料表：{', '.join(result_info['tables'])}\n"
            combined_result += f"內容：{result_info['result']}\n\n"
        
        return combined_result
        