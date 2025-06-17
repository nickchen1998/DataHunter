from langchain.agents import OpenAIFunctionsAgent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from symptoms.models import Symptom, SYMPTOM_PROMPT_TEMPLATE
from symptoms.tools import SymptomDataRetrievalTool




class ChatAgent:
    TOOL_FACTORY = {
        Symptom.__name__: SymptomDataRetrievalTool,
    }

    SYSTEM_PROMPT_TEMPLATE_FACTORY = {
        Symptom.__name__: SYMPTOM_PROMPT_TEMPLATE,
    }
    
    def process_query(self, user_question: str, reference_id_list: list[int], data_type: str = "Mixed") -> str:
        # 動態組 prompt
        if reference_id_list:
            reference_str = f"請使用我指定的參考資料ID（格式為 JSON，例如：[1, 2, 3]）：{reference_id_list}。"
            user_question += "\n" + reference_str

        # Tool 與 Prompt 準備
        tool = self.TOOL_FACTORY[data_type]()
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.SYSTEM_PROMPT_TEMPLATE_FACTORY[data_type]),
            # MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # ✅ 產生 agent chain
        agent = OpenAIFunctionsAgent(
            llm=llm,
            tools=[tool],
            prompt=prompt
        )

        # ✅ 包裝成 Executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=[tool],
            verbose=True,  # 可視需求加上
            return_intermediate_steps=True
        )

        # ✅ 呼叫 Executor，取得結構化結果
        result = agent_executor.invoke({"input": user_question})

        # 取得回答與 Tool 回傳的原始資料
        response = result["output"]
        steps = result["intermediate_steps"]

        # ✅ 嘗試解析回傳的 id list
        id_list = None
        if steps:
            _, tool_output = steps[-1]
            if isinstance(tool_output, tuple) and isinstance(tool_output[1], list):
                id_list = tool_output[1]

        # ✅ 組合最終結果
        response += f"\n\n📄 參考資料 ID：{id_list if id_list else '無'}"
        response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，實際應用時請諮詢相關專業人士。"

        return response
    