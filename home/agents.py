from langchain.agents import OpenAIFunctionsAgent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from symptoms.models import Symptom, SYMPTOM_SYSTEM_PROMPT
from symptoms.tools import SymptomDataRetrievalTool




class ChatAgent:
    TOOL_FACTORY = {
        Symptom.__name__: SymptomDataRetrievalTool,
    }

    SYSTEM_PROMPT_FACTORY = {
        Symptom.__name__: SYMPTOM_SYSTEM_PROMPT,
    }
    
    def process_query(self, user_question: str, reference_id_list: list[int], data_type: str = "Mixed") -> str:
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

        agent = OpenAIFunctionsAgent(
            llm=llm,
            tools=[tool],
            prompt=prompt
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=[tool],
            verbose=True,
            return_intermediate_steps=True
        )

        result = agent_executor.invoke({"input": user_question})

        response = result["output"]
        steps = result["intermediate_steps"]

        final_reference_id_list = None
        if steps:
            _, tool_output = steps[-1]
            if isinstance(tool_output, tuple) and isinstance(tool_output[1], list):
                final_reference_id_list = tool_output[1]

        response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，實際應用時請諮詢相關專業人士。"

        return response, final_reference_id_list
    