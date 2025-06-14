import io
import hashlib
import requests
import pandas as pd
import json
import psycopg2
import xml.etree.ElementTree as ET
from gov_datas.models import Dataset, File
from DataHunter.celery import app
from langchain_openai import OpenAIEmbeddings
from django.conf import settings
from utils.str_date import parse_datetime_string


@app.task()
def period_crawl_government_datasets(demo=False):
    url = "https://data.gov.tw/api/front/dataset/export?format=csv"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    
    supported_formats = ['CSV', 'XML', 'JSON']
    filtered_df = df[df['檔案格式'].str.contains('|'.join(supported_formats), case=False, na=False)]
    categories = filtered_df['服務分類'].unique()

    if demo:
        categories = ['投資理財']

    processed_datasets = 0

    for category in categories:
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
                    'columns_description': row.主要欄位說明.split(';') if pd.notna(row.主要欄位說明) else [],
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

            print(f"{'創建' if created else '更新'} 資料集: {dataset.name}")
            if demo:
                process_dataset_files(row.to_dict(), dataset.id)
            else:
                process_dataset_files.delay(row.to_dict(), dataset.id)
            processed_datasets += 1

    print(f"共處理 {processed_datasets} 筆資料。")


@app.task()
def process_dataset_files(data: dict, dataset_id: int):
    dataset = Dataset.objects.get(id=dataset_id)
    data = pd.Series(data)

    if pd.isna(data.檔案格式) or pd.isna(data.資料下載網址) or pd.isna(data.編碼格式):
        return

    file_formats = str(data.檔案格式).split(';')
    download_urls = str(data.資料下載網址).split(';')
    encodings = str(data.編碼格式).split(';')

    seen_md5 = set()
    new_tables = []

    for file_format, download_url, encoding in zip(file_formats, download_urls, encodings):
        file_format = file_format.strip().lower()
        download_url = download_url.strip()
        encoding = encoding.strip()

        if file_format not in ['csv', 'xml', 'json']:
            continue

        try:
            response = requests.get(download_url, verify=False, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"下載檔案失敗 {download_url}: {str(e)}")
            continue
        
        try:
            df = _read_file_to_dataframe(response.content, file_format, encoding)
        except Exception as e:
            print(f"讀取檔案失敗 {download_url}: {str(e)}")
            continue
        
        if df is None or df.empty:
            continue
            
        df_md5 = _get_dataframe_md5(df)

        if df_md5 in seen_md5:
            print(f"內容重複（不同格式但內容相同），跳過: {download_url}")
            continue

        # 檢查是否有相同內容的檔案已存在
        if File.objects.filter(content_md5=df_md5).exists():
            print(f"相同內容的檔案已存在 (MD5: {df_md5})，跳過: {download_url}")
            continue

        try:
            seen_md5.add(df_md5)
            table_name = f"{dataset.dataset_id}_{df_md5[:8]}"
            
            # 儲存資料到資料表並創建 File 記錄
            if _save_dataframe_to_table(dataset, df, table_name, download_url, file_format, df_md5, encoding):
                new_tables.append(table_name)
                print(f"成功處理檔案，建立資料表: {table_name}")
            else:
                print(f"儲存檔案失敗: {download_url}")
        except Exception as e:
            seen_md5.remove(df_md5)
            print(f"儲存檔案失敗 {download_url}: {str(e)}")
    
    # 處理完成，新資料表會透過 File model 記錄
    if new_tables:
        print(f"成功為資料集 {dataset.name} 創建了 {len(new_tables)} 個資料表")


def _read_file_to_dataframe(content, file_format, encoding):
    try:
        decoded_content = content.decode(encoding, errors='ignore')
        
        if file_format == 'csv':
            return pd.read_csv(io.StringIO(decoded_content))
        
        elif file_format == 'json':
            json_data = json.loads(decoded_content)
            
            if isinstance(json_data, list):
                return pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                for value in json_data.values():
                    if isinstance(value, list) and len(value) > 0:
                        return pd.DataFrame(value)

                return pd.DataFrame([json_data])
            
        elif file_format == 'xml':
            root = ET.fromstring(decoded_content)
            
            data = []
            for child in root:
                row = {subchild.tag: subchild.text for subchild in child}
                if row:
                    data.append(row)
            
            if data:
                return pd.DataFrame(data)
            else:
                row = {child.tag: child.text for child in root}
                if row:
                    return pd.DataFrame([row])
                    
    except Exception as e:
        print(f"讀取 {file_format} 格式失敗: {str(e)}")
        
    return None


def _save_dataframe_to_table(dataset, df, table_name, download_url, file_format, content_md5, encoding):
    try:
        # 在 DataFrame 中添加元資料欄位
        df_with_meta = df.copy()
        df_with_meta['_dataset_id'] = dataset.dataset_id
        df_with_meta['_original_url'] = download_url
        df_with_meta['_original_format'] = file_format
        df_with_meta['_content_md5'] = content_md5
        df_with_meta['_created_at'] = pd.Timestamp.now()
        
        # 創建資料表
        if not create_table_from_dataframe(df_with_meta, table_name):
            return False
        
        # 創建 File 記錄
        File.objects.create(
            dataset=dataset,
            original_download_url=download_url,
            original_format=file_format,
            encoding=encoding,
            content_md5=content_md5,
            table_name=table_name,
        )
        
        return True
    except Exception as e:
        print(f"儲存 DataFrame 到資料表 {table_name} 失敗: {str(e)}")
        return False


def _get_dataframe_md5(df: pd.DataFrame) -> str:
    df_copy = df.copy().astype(str)
    df_copy = df_copy[sorted(df_copy.columns)]
    df_copy = df_copy.sort_values(by=sorted(df_copy.columns)).reset_index(drop=True)
    
    content_str = df_copy.to_csv(index=False)
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()


def create_table_from_dataframe(df: pd.DataFrame, table_name: str):
    try:
        db_config = settings.DATABASES['govdata']
        conn = psycopg2.connect(
            host=db_config['HOST'],
            port=db_config['PORT'],
            database=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD']
        )
        create_sql = _generate_create_table_sql(df, table_name)
        
        with conn.cursor() as cursor:
            cursor.execute(create_sql)
            conn.commit()
            
            # 插入資料
            _insert_dataframe_to_table(cursor, df, table_name)
            conn.commit()
            
        return True
    except Exception as e:
        print(f"創建資料表 {table_name} 失敗: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def _generate_create_table_sql(df: pd.DataFrame, table_name: str) -> str:
    columns = []
    for col in df.columns:
        # 簡單的型別推斷
        if df[col].dtype == 'object':
            col_type = 'TEXT'
        elif df[col].dtype == 'int64':
            col_type = 'BIGINT'
        elif df[col].dtype == 'float64':
            col_type = 'DOUBLE PRECISION'
        elif df[col].dtype == 'bool':
            col_type = 'BOOLEAN'
        else:
            col_type = 'TEXT'
        
        columns.append(f'"{col}" {col_type}')
    
    columns_sql = ', '.join(columns)
    return f'CREATE TABLE "{table_name}" ({columns_sql})'


def _insert_dataframe_to_table(cursor, df: pd.DataFrame, table_name: str):
    if df.empty:
        return
    
    # 準備插入語句
    columns = [f'"{col}"' for col in df.columns]
    placeholders = ['%s'] * len(df.columns)
    
    insert_sql = f"""
        INSERT INTO "{table_name}" ({', '.join(columns)}) 
        VALUES ({', '.join(placeholders)})
    """
    
    # 批量插入資料
    values = []
    for _, row in df.iterrows():
        row_values = []
        for val in row:
            if pd.isna(val):
                row_values.append(None)
            else:
                row_values.append(str(val))
        values.append(tuple(row_values))
    
    cursor.executemany(insert_sql, values)
