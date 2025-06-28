import io
import requests
import pandas as pd
from crawlers.models import Dataset, File, ASSOCIATED_CATEGORIES_DATABASE_NAME
from RAGPilot.celery import app
from langchain_openai import OpenAIEmbeddings
from django.conf import settings
from utils.str_date import parse_datetime_string
from utils.file_to_df import FileDataFrameHandler
from fake_useragent import UserAgent


@app.task()
def period_crawl_government_datasets(demo=False):
    url = "https://data.gov.tw/api/front/dataset/export?format=csv"
    response = requests.get(url, timeout=30, headers={'User-Agent': UserAgent().random})
    response.raise_for_status()

    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    
    supported_formats = ['CSV', 'XML', 'JSON']
    filtered_df = df[df['檔案格式'].str.contains('|'.join(supported_formats), case=False, na=False)]
    categories = filtered_df['服務分類'].unique()

    if demo:
        categories = ['投資理財']

    processed_datasets = 0

    for category in [tmp for tmp in categories if tmp in ASSOCIATED_CATEGORIES_DATABASE_NAME]:
        sub_df = filtered_df[filtered_df['服務分類'] == category]
        for _, row in sub_df.iterrows():
            dataset, created = Dataset.objects.update_or_create(
                dataset_id=row.資料集識別碼,
                defaults={
                    'url': f"https://data.gov.tw/dataset/{row.資料集識別碼}",
                    'name': row.資料集名稱,
                    'category': row.服務分類,
                    'description': row.資料集描述,
                    'description_embeddings': OpenAIEmbeddings(
                        model="text-embedding-3-small").embed_query(row.資料集描述),
                    'department': row.提供機關,
                    'update_frequency': row.更新頻率,
                    'license': row.授權方式,
                    'price': row.計費方式,
                    'contact_person': row.提供機關聯絡人姓名 if pd.notna(row.提供機關聯絡人姓名) else None,
                    'contact_phone': row.提供機關聯絡人電話 if pd.notna(row.提供機關聯絡人電話) else None,
                    'upload_time': parse_datetime_string(row.上架日期),
                    'update_time': parse_datetime_string(row.詮釋資料更新時間),
                }
            )

            if created:
                print(f"新增資料集: {dataset.name}")
            
            if demo:
                process_dataset_files(row.to_dict(), dataset.id)
            else:
                process_dataset_files.delay(row.to_dict(), dataset.id)
            processed_datasets += 1

    print(f"完成處理 {processed_datasets} 個資料集")


@app.task()
def process_dataset_files(data: dict, dataset_id: int):
    dataset = Dataset.objects.get(id=dataset_id)
    data = pd.Series(data)

    if pd.isna(data.檔案格式) or pd.isna(data.資料下載網址) or pd.isna(data.編碼格式) or pd.isna(data.主要欄位說明):
        return

    file_formats = str(data.檔案格式).split(';')
    download_urls = str(data.資料下載網址).split(';')
    encodings = str(data.編碼格式).split(';')

    handler = FileDataFrameHandler()
    seen_md5 = set()
    new_tables = []

    for file_format, download_url, encoding in zip(file_formats, download_urls, encodings):
        file_format = file_format.strip().lower()
        download_url = download_url.strip()
        encoding = encoding.strip()

        if file_format not in ['csv', 'xml', 'json']:
            continue

        try:
            response = requests.get(download_url, verify=False, timeout=30, headers={'User-Agent': UserAgent().random})
            response.raise_for_status()
        except Exception as e:
            print(f"下載失敗 {download_url}: {str(e)}")
            continue
        
        try:
            df = handler.convert_to_dataframe(response.content, file_format, encoding)
        except Exception as e:
            print(f"讀取失敗 {download_url}: {str(e)}")
            continue
        
        if df is None or df.empty:
            continue
            
        df_md5 = handler.get_dataframe_md5(df)

        if df_md5 in seen_md5:
            continue

        if File.objects.filter(content_md5=df_md5).exists():
            continue

        try:
            seen_md5.add(df_md5)
            
            column_description = data.主要欄位說明.split(';') if pd.notna(data.主要欄位說明) else []
            success, result = _process_and_save_dataset_file(
                handler, df, dataset, download_url, file_format, encoding, column_description
            )
            
            if success:
                new_tables.append(result)
            else:
                print(f"儲存失敗 {download_url}: {result}")
        except Exception as e:
            seen_md5.discard(df_md5)
            print(f"處理失敗 {download_url}: {str(e)}")
    
    if new_tables:
        print(f"資料集 {dataset.name} 新增 {len(new_tables)} 個檔案")


def _process_and_save_dataset_file(handler: FileDataFrameHandler, df: pd.DataFrame, 
                                 dataset: Dataset, download_url: str, file_format: str, 
                                 encoding: str, column_description: list) -> tuple[bool, str]:
    if df is None or df.empty:
        return False, "DataFrame 為空"
    
    content_md5 = handler.get_dataframe_md5(df)
    
    if File.objects.filter(content_md5=content_md5).exists():
        return False, "相同內容的檔案已存在"
    
    table_name = f"{dataset.dataset_id}_{content_md5}"
    database_name = ASSOCIATED_CATEGORIES_DATABASE_NAME[dataset.category]
    
    try:
        processed_df = _prepare_dataframe_for_dataset_storage(
            handler, df, dataset, download_url, file_format, content_md5
        )
        
        column_mapping_list = _create_column_mapping_list(
            handler, df, column_description
        )
        
        success, message = handler.save_to_database(
            processed_df, table_name, database_name
        )
        
        if success:
            File.objects.create(
                dataset=dataset,
                original_download_url=download_url,
                original_format=file_format,
                encoding=encoding,
                content_md5=content_md5,
                table_name=table_name,
                database_name=database_name,
                column_mapping_list=column_mapping_list,
            )
            
            return True, table_name
        else:
            return False, message
            
    except Exception as e:
        return False, f"儲存失敗: {str(e)}"


def _prepare_dataframe_for_dataset_storage(handler: FileDataFrameHandler, df: pd.DataFrame, 
                                         dataset: Dataset, download_url: str, 
                                         file_format: str, content_md5: str) -> pd.DataFrame:
    processed_df = handler.rename_dataframe_columns_to_excel_style(df)
    
    processed_df['_dataset_id'] = dataset.dataset_id
    processed_df['_original_url'] = download_url
    processed_df['_original_format'] = file_format
    processed_df['_content_md5'] = content_md5
    processed_df['_created_at'] = pd.Timestamp.now()
    
    return processed_df


def _create_column_mapping_list(handler: FileDataFrameHandler, df: pd.DataFrame, 
                              column_description: list) -> list:
    num_columns = len(df.columns)
    excel_column_names = handler.generate_excel_column_names(num_columns)
    
    column_mapping_list = []
    for i, new_col in enumerate(excel_column_names):
        current_column_desc = column_description[i] if i < len(column_description) else f"欄位_{i+1}"
        column_mapping_list.append([new_col, current_column_desc])
    
    return column_mapping_list


