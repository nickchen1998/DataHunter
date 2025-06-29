import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from RAGPilot.celery import app
from sources.models import SourceFile, SourceFileChunk, SourceFileTable, ProcessingStatus
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from utils.file_to_df import FileDataFrameHandler


@app.task()
def extract_pdf_soruce_file_content(source_file_id: int):
    try:
        source_file = SourceFile.objects.get(id=source_file_id)
        source_file.status = ProcessingStatus.PROCESSING
        source_file.save()
        source_file.refresh_from_db()
        
        # 使用 PyPDFLoader 載入 PDF
        loader = PyPDFLoader(source_file.path)
        documents = loader.load()
        
        if not documents:
            print(f"PDF 檔案 {source_file.filename} 沒有可提取的內容")
            source_file.status = ProcessingStatus.COMPLETED
            source_file.save()
            return
                
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=150,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        chunk_embeddings = embeddings.embed_documents(chunks)
        
        chunks_created = 0
        for i, (chunk_text, embedding) in enumerate(zip(chunks, chunk_embeddings)):
            SourceFileChunk.objects.create(
                user=source_file.user,
                source_file=source_file,
                content=chunk_text,
                content_embedding=embedding
            )
            chunks_created += 1
        
        source_file.status = ProcessingStatus.COMPLETED
        source_file.save()
        source_file.refresh_from_db()
        
        return f"成功提取 PDF 檔案 {source_file.filename} 的內容，創建了 {chunks_created} 個文字片段"

    except Exception as e:
        source_file = SourceFile.objects.get(id=source_file_id)
        source_file.status = ProcessingStatus.FAILED
        source_file.save()
        
        return f"提取 PDF 內容失敗: {str(e)}"


@app.task()
def extract_structured_data_from_source_file(source_file_id: int):
    """
    使用 FileDataFrameHandler 提取結構化資料
    """
    try:
        # 獲取 SourceFile 物件
        source_file = SourceFile.objects.get(id=source_file_id)
        
        # 檢查檔案格式是否為結構化資料
        supported_formats = ['csv', 'json', 'xml']
        if source_file.format not in supported_formats:
            print(f"檔案 {source_file.filename} 格式 {source_file.format} 不支援結構化資料提取")
            return
        
        # 更新處理狀態
        source_file.status = ProcessingStatus.PROCESSING
        source_file.save()
        
        # 構建檔案的完整路徑
        if not source_file.path:
            raise ValueError(f"檔案 {source_file.filename} 沒有檔案路徑")
        
        # 檔案的完整路徑
        file_path = os.path.join(settings.BASE_DIR, 'source_files', source_file.path.lstrip('/'))
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"檔案不存在: {file_path}")
        
        # 讀取檔案內容
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 初始化 FileDataFrameHandler
        handler = FileDataFrameHandler()
        
        # 將檔案內容轉換為 DataFrame
        df = handler.convert_to_dataframe(file_content, source_file.format, encoding='utf-8')
        
        if df is None or df.empty:
            print(f"檔案 {source_file.filename} 沒有可提取的結構化資料")
            source_file.status = ProcessingStatus.COMPLETED
            source_file.save()
            return
        
        # 生成資料表名稱
        table_name = f"user_{source_file.user.id}_source_{source_file.id}_{source_file.uuid.hex[:8]}"
        database_name = f"source_data_user_{source_file.user.id}"
        
        # 使用 FileDataFrameHandler 儲存到資料庫
        success, message = handler.save_to_database(df, table_name, database_name)
        
        if success:
            # 創建 SourceFileTable 記錄
            SourceFileTable.objects.create(
                user=source_file.user,
                source_file=source_file,
                table_name=table_name,
                database_name=database_name
            )
            
            # 生成檔案摘要（基於資料結構和前幾行資料）
            summary_parts = []
            summary_parts.append(f"資料表包含 {len(df)} 行和 {len(df.columns)} 欄")
            summary_parts.append(f"欄位名稱: {', '.join(df.columns[:10].astype(str))}")  # 只顯示前10個欄位
            if len(df.columns) > 10:
                summary_parts.append(f"... 及其他 {len(df.columns) - 10} 個欄位")
            
            # 添加前幾行的樣本資料
            if len(df) > 0:
                sample_data = df.head(3).to_string(max_cols=5, max_colwidth=50)
                summary_parts.append(f"樣本資料:\n{sample_data}")
            
            summary_content = "\n".join(summary_parts)
            
            # 生成摘要的嵌入向量
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            summary_embedding = embeddings.embed_query(summary_content)
            
            # 更新 SourceFile 的摘要和嵌入
            source_file.summary = summary_content
            source_file.summary_embedding = summary_embedding
            source_file.status = ProcessingStatus.COMPLETED
            source_file.save()
            
            print(f"成功提取結構化資料 {source_file.filename}，創建資料表 {table_name}")
            
        else:
            raise Exception(f"儲存資料到資料庫失敗: {message}")
            
    except ObjectDoesNotExist:
        print(f"找不到 ID 為 {source_file_id} 的 SourceFile")
    except Exception as e:
        print(f"提取結構化資料失敗: {str(e)}")
        # 更新處理狀態為失敗
        try:
            source_file = SourceFile.objects.get(id=source_file_id)
            source_file.status = ProcessingStatus.FAILED
            source_file.save()
        except:
            pass