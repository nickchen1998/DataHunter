import json
from django.contrib.auth import get_user_model
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
from RAGPilot.celery import app
from utils.nl_to_sql import CustomNL2SQLQueryTool
from symptoms.models import Symptom, SYMPTOM_SYSTEM_PROMPT
from symptoms.tools import SymptomDataRetrievalTool
from gov_datas.models import Dataset, GOV_DATA_SYSTEM_PROMPT
from gov_datas.tools import GovDataDatasetQueryTool
from conversations.models import Session, Message
User = get_user_model()


class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, session, user, ai_message):
        self.session = session
        self.user = user
        self.ai_message = ai_message
        self.tool_results = []

        
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("🤖 LLM 開始處理...")
        
    def on_llm_end(self, response, **kwargs):
        print("🎯 LLM 完成回應")
        if hasattr(response, 'generations') and response.generations:
            content = response.generations[0][0].text
            self.ai_message.text = content
            self.ai_message.save()
            print(f"💬 AI 回應: {content[:100]}...")
            
    def on_agent_action(self, action, **kwargs):
        print(f"🎬 Agent 動作: {action.tool} - {action.tool_input}")
        
    def on_agent_finish(self, finish, **kwargs):
        print(f"🏁 Agent 完成: {finish.return_values.get('output', '')[:100]}...")
    



@app.task()
def process_conversation_async(user_id, user_question, reference_id_list=None, data_type="Mixed", user_message_id=None, ai_message_id=None):
    try:
        user = User.objects.get(id=user_id)
        
        session = Session.get_or_create_user_session(user)
        
        if ai_message_id:
            ai_message = Message.objects.get(id=ai_message_id)
        else:
            ai_message = Message.create_ai_message(session, user, "")
        
        if reference_id_list:
            user_question_with_refs = f"請使用我指定的參考資料ID：\n{reference_id_list}\n我的問題是：\n{user_question}"
        else:
            user_question_with_refs = user_question
            
        tool_factory = {
            Symptom.__name__: SymptomDataRetrievalTool,
            Dataset.__name__: GovDataDatasetQueryTool,
        }
        
        system_prompt_factory = {
            Symptom.__name__: SYMPTOM_SYSTEM_PROMPT,
            Dataset.__name__: GOV_DATA_SYSTEM_PROMPT,
        }
        
        tool = tool_factory[data_type]()
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt_factory[data_type]),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        tools = [tool, CustomNL2SQLQueryTool()]
        
        agent = create_openai_functions_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )
        
        callback_handler = StreamingCallbackHandler(session, user, ai_message)
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=3,
            callbacks=[callback_handler]
        )
        
        print(f"🚀 開始處理對話: {user_question[:50]}...")
        result = agent_executor.invoke({"input": user_question_with_refs})
        print(f"🎉 對話處理完成!")
        
        # 記錄 Tool 執行結果到資料庫（但不顯示在前端）
        if 'intermediate_steps' in result and result['intermediate_steps']:
            print(f"🔧 記錄 {len(result['intermediate_steps'])} 個工具調用結果到資料庫")
            
            for i, (action, observation) in enumerate(result['intermediate_steps']):
                # 寫入資料庫，並關聯到 AI Message
                tool_message = Message.create_tool_message_with_parent(
                    session=session,
                    user=user,
                    parent_message=ai_message,
                    tool_name=action.tool,
                    tool_params=action.tool_input,
                    tool_result=str(observation)
                )
                
                # 同時記錄到 callback handler
                callback_handler.tool_results.append({
                    'tool_name': action.tool,
                    'tool_input': action.tool_input,
                    'tool_output': str(observation),
                    'index': i,
                    'message_id': tool_message.id,
                    'parent_message_id': ai_message.id
                })
                
                print(f"💾 工具 {i+1} 已寫入資料庫: ID={tool_message.id}, Tool={action.tool}, 關聯到 AI Message={ai_message.id}")
                print(f"📄 結果預覽: {str(observation)[:200]}...")
        
        # 最後更新 AI 訊息，確保它的 updated_at 是最新的
        final_output = result.get('output', '')
        if final_output:
            ai_message.text = final_output
            ai_message.save()
            print(f"💾 最終 AI 訊息已更新: {final_output[:100]}...")
        
        return {
            'status': 'completed',
            'response': result.get('output', ai_message.text),
            'user_message_id': user_message_id,
            'ai_message_id': ai_message.id,
            'tool_results': callback_handler.tool_results,
            'session_id': session.id
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


