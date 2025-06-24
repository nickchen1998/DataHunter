from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from utils.nl_to_sql import CustomNL2SQLQueryTool
import json

from symptoms.models import Symptom, SYMPTOM_SYSTEM_PROMPT
from symptoms.tools import SymptomDataRetrievalTool

from gov_datas.models import Dataset, GOV_DATA_SYSTEM_PROMPT
from gov_datas.tools import GovDataDatasetQueryTool

from conversations.models import Session, Message


class ChatAgent:
    TOOL_FACTORY = {
        Symptom.__name__: SymptomDataRetrievalTool,
        Dataset.__name__: GovDataDatasetQueryTool,
    }

    SYSTEM_PROMPT_FACTORY = {
        Symptom.__name__: SYMPTOM_SYSTEM_PROMPT,
        Dataset.__name__: GOV_DATA_SYSTEM_PROMPT,
    }
    
    def process_query(self, user_question: str, reference_id_list: list[int], user, data_type: str = "Mixed") -> str:
        """處理用戶查詢並記錄對話"""
        # 取得或建立用戶的 session
        session = Session.get_or_create_user_session(user)
        # 記錄用戶訊息
        Message.create_user_message(session, user, user_question)

        if reference_id_list:
            user_question = f"請使用我指定的參考資料ID：\n{reference_id_list}\n我的問題是：\n{user_question}"

        tool = self.TOOL_FACTORY[data_type]()
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.SYSTEM_PROMPT_FACTORY[data_type]),
            # MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        tools = [tool, CustomNL2SQLQueryTool()]
        
        agent = create_openai_functions_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=3
        )

        result = agent_executor.invoke({"input": user_question})

        response = result["output"]
        steps = result["intermediate_steps"]

        # 記錄所有工具調用
        self._log_tool_calls(session, user, steps)

        response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，實際應用時請諮詢相關專業人士。"

        # 記錄 AI 回覆
        Message.create_ai_message(session, user, response)

        return response

    def _log_tool_calls(self, session, user, steps):
        """記錄所有工具調用"""
        for step in steps:
            agent_action, tool_output = step
            
            # 提取工具名稱和參數
            tool_name = agent_action.tool
            tool_params = agent_action.tool_input
            
            # 記錄工具調用
            Message.create_tool_message(
                session=session,
                user=user,
                tool_name=tool_name,
                tool_params=json.loads(json.dumps(tool_params, default=str)),
                tool_result=tool_output
            )
    