from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

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
            tool = self.TOOL_FACTORY[data_type]()
            response = tool.invoke(dict(
                reference_id_list=reference_id_list,
                question=user_question,
            ))
            
        else:
            agent = initialize_agent(
                tools=[tmp() for tmp in self.TOOL_FACTORY.values()],
                agent=AgentType.OPENAI_FUNCTIONS,
                llm=ChatOpenAI(model="gpt-4o", temperature=0.7),
            )            
            response = agent.run(user_question)
            
        response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，實際應用時請諮詢相關專業人士。"
        return response
    