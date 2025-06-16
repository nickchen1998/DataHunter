from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


class ChatAgent:
    """醫療聊天代理，負責基於參考資料或自身知識回答問題"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        self.embeddings = OpenAIEmbeddings()
    
    def process_query(self, user_question: str, references: List[Dict[str, Any]] = None) -> str:
        """處理用戶查詢"""
        try:
            # 如果有參考資料，優先使用參考資料回答
            if references and len(references) > 0:
                return self._answer_with_references(user_question, references)
            
            # 沒有參考資料時，使用自身知識回答
            return self._answer_without_references(user_question)
            
        except Exception as e:
            return f"處理查詢時發生錯誤：{str(e)}"
    
    def _answer_with_references(self, user_question: str, references: List[Dict[str, Any]]) -> str:
        """基於參考資料回答問題"""
        try:
            # 準備參考資料文檔
            documents = []
            for ref in references:
                doc_content = f"科別：{ref['department']}\n性別：{ref['gender']}\n主訴：{ref['symptom']}\n問題：{ref['question']}\n回答：{ref['answer']}"
                documents.append(Document(page_content=doc_content))
            
            if not documents:
                return self._answer_without_references(user_question)
            
            # 創建向量存儲
            vectorstore = FAISS.from_documents(documents, self.embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": min(len(documents), 5)})
            
            # 創建提示模板
            system_prompt = """你是一個專業的醫療資訊助手。請根據用戶提供的參考資料回答問題。

回答原則：
1. **優先使用參考資料**：主要基於用戶選擇的參考資料進行回答
2. **靈活解釋**：可以基於參考資料進行合理的解釋、總結和建議
3. **適度延伸**：如果參考資料相關但不完全匹配，可以進行適度的專業延伸
4. **明確來源**：清楚說明回答是基於用戶提供的參考資料
5. **專業提醒**：始終提醒這些資料僅供參考，具體診斷需諮詢專業醫師

用戶提供的參考資料：
{context}

用戶問題：{input}

請基於以上參考資料詳細回答用戶問題。如果參考資料中沒有直接答案，請基於相關資料提供有用的建議和資訊。"""

            prompt = ChatPromptTemplate.from_template(system_prompt)
            
            # 創建文檔鏈
            document_chain = create_stuff_documents_chain(self.llm, prompt)
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            
            # 執行查詢
            result = retrieval_chain.invoke({"input": user_question})
            
            # 添加資料來源說明
            response = result["answer"]
            response += f"\n\n📊 **回答依據**：基於您選擇的 {len(references)} 筆參考資料"
            response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，具體診斷和治療建議請諮詢專業醫師。"
            
            return response
            
        except Exception as e:
            return f"處理參考資料時發生錯誤：{str(e)}。請檢查您的參考資料是否正確。"
    
    def _answer_without_references(self, user_question: str) -> str:
        """沒有參考資料時的回答策略"""
        try:
            # 創建提示模板
            system_prompt = """你是一個專業的醫療資訊助手。用戶沒有提供參考資料，請基於你的醫療知識回答問題。

回答原則：
1. **明確說明**：請務必告訴使用者他沒有選擇參考資料，所以資訊可能會不正確。
2. **專業回答**：提供專業、準確的醫療資訊
3. **建議參考資料**：建議用戶選擇相關的參考資料以獲得更準確的資訊
4. **專業提醒**：強調需要諮詢專業醫師

用戶問題：{input}

請按照以上原則回答問題。"""

            prompt = ChatPromptTemplate.from_template(system_prompt)
            
            # 創建鏈
            chain = prompt | self.llm
            
            # 執行查詢
            result = chain.invoke({"input": user_question})
            
            response = result.content
            response += f"\n\n💡 **建議**：您可以從右側資料列表中選擇相關的參考資料，這樣我就能提供更準確、更具體的回答。"
            response += f"\n\n⚠️ **重要提醒**：以上資訊僅供參考，具體診斷和治療建議請諮詢專業醫師。"
            
            return response
            
        except Exception as e:
            return f"我有注意到您沒有選擇參考資料，但以我的認知，關於「{user_question}」這個問題，建議您：\n\n1. 選擇相關的參考資料以獲得更準確的資訊\n2. 諮詢專業醫師獲得個人化的建議\n\n💡 **提示**：您可以從右側資料列表中點擊「加入對話當中作為參考資料」來添加相關資料。\n\n⚠️ **重要提醒**：任何醫療問題都應該諮詢專業醫師。" 