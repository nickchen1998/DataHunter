from RAGPilot.celery import app


@app.task()
def extract_pdf_soruce_file_content(source_file_id: int):
    """
    使用 LangChain PDFLoader 提取 PDF 檔案的內容
    """
    pass


@app.task()
def extract_structured_data_from_source_file(source_file_id: int):
    """
    使用 LangChain 提取結構化資料
    """
    pass