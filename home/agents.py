from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

from symptoms.models import Symptom
from symptoms.tools import SymptomDataRetrievalTool

from gov_datas.models import Dataset



class ChatAgent:
    TOOL_FACTORY = {
        Symptom.__name__: SymptomDataRetrievalTool,
        # Dataset.__name__: DatasetDataRetrievalTool
    }
    
    def process_query(self, user_question: str, reference_id_list: list[int], data_type: str = "Mixed") -> str:
        if reference_id_list:
            specific_reference_id_prompt = "請使用我指定的參考資料ID，並以json格式傳遞（例如：[1, 2, 3]），以便進行搜尋以及回答："
            for reference_id in reference_id_list:
                specific_reference_id_prompt += f"{reference_id}、"
            user_question = user_question + specific_reference_id_prompt

        tool = self.TOOL_FACTORY[data_type]()
        agent = initialize_agent(
            tools=[tool],
            agent=AgentType.OPENAI_FUNCTIONS,
            llm=ChatOpenAI(model="gpt-4o", temperature=0.7),
        )            
        response = agent.run(user_question)
        response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，實際應用時請諮詢相關專業人士。"

        return response
    