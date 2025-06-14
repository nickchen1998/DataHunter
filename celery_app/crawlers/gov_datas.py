import io
import hashlib
import requests
import pandas as pd
import json
import psycopg2
import xml.etree.ElementTree as ET
from gov_datas.models import Dataset, File, ASSOCIATED_CATEGORIES_DATABASE_NAME
from DataHunter.celery import app
from langchain_openai import OpenAIEmbeddings
from django.conf import settings
from utils.str_date import parse_datetime_string
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
        _check_database_exists(category)
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
            response = requests.get(download_url, verify=False, timeout=30, headers={'User-Agent': UserAgent().random})
            response.raise_for_status()
        except Exception as e:
            print(f"下載失敗 {download_url}: {str(e)}")
            continue
        
        try:
            df = _read_file_to_dataframe(response.content, file_format, encoding)
        except Exception as e:
            print(f"讀取失敗 {download_url}: {str(e)}")
            continue
        
        if df is None or df.empty:
            continue
            
        df_md5 = _get_dataframe_md5(df)

        if df_md5 in seen_md5:
            continue

        # 檢查是否有相同內容的檔案已存在
        if File.objects.filter(content_md5=df_md5).exists():
            continue

        try:
            seen_md5.add(df_md5)
            table_name = f"{dataset.dataset_id}_{df_md5}"
            
            # 儲存資料到資料表並創建 File 記錄
            if _save_dataframe_to_table(dataset, df, table_name, download_url, file_format, df_md5, encoding):
                new_tables.append(table_name)
            else:
                print(f"儲存失敗: {download_url}")
        except Exception as e:
            seen_md5.remove(df_md5)
            print(f"處理失敗 {download_url}: {str(e)}")
    
    # 處理完成，新資料表會透過 File model 記錄
    if new_tables:
        print(f"資料集 {dataset.name} 新增 {len(new_tables)} 個檔案")


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
        # 驗證 DataFrame 結構
        if df.empty:
            print(f"DataFrame 為空，跳過: {download_url}")
            return False
            
        # 檢查是否有重複的欄位名稱
        if len(df.columns) != len(set(df.columns)):
            print(f"發現重複欄位名稱，重新命名: {download_url}")
            df.columns = [f"{col}_{i}" if list(df.columns).count(col) > 1 else col 
                         for i, col in enumerate(df.columns)]
        
        # 確保所有欄位名稱都是字串
        df.columns = [str(col) for col in df.columns]
        
        # 在 DataFrame 中添加元資料欄位
        df_with_meta = df.copy()
        df_with_meta['_dataset_id'] = dataset.dataset_id
        df_with_meta['_original_url'] = download_url
        df_with_meta['_original_format'] = file_format
        df_with_meta['_content_md5'] = content_md5
        df_with_meta['_created_at'] = pd.Timestamp.now()
        
        # 創建資料表
        if not create_table_from_dataframe(df_with_meta, table_name, dataset.category):
            return False
        
        # 創建 File 記錄
        File.objects.create(
            dataset=dataset,
            original_download_url=download_url,
            original_format=file_format,
            encoding=encoding,
            content_md5=content_md5,
            table_name=table_name,
            database_name=ASSOCIATED_CATEGORIES_DATABASE_NAME[dataset.category],
        )
        
        return True
    except Exception as e:
        print(f"儲存失敗 {table_name}: {str(e)}")
        return False


def _get_dataframe_md5(df: pd.DataFrame) -> str:
    df_copy = df.copy().astype(str)
    df_copy = df_copy[sorted(df_copy.columns)]
    df_copy = df_copy.sort_values(by=sorted(df_copy.columns)).reset_index(drop=True)
    
    content_str = df_copy.to_csv(index=False)
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()


def create_table_from_dataframe(df: pd.DataFrame, table_name: str, category: str):
    try:
        db_config = settings.DATABASES['default']
        conn = psycopg2.connect(
            host=db_config['HOST'],
            port=db_config['PORT'],
            database=ASSOCIATED_CATEGORIES_DATABASE_NAME[category],
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
        print(f"建表失敗 {table_name}: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def _generate_create_table_sql(df: pd.DataFrame, table_name: str) -> str:
    columns = []
    for col in df.columns:
        col_type = _infer_column_type(df[col])
        columns.append(f'"{col}" {col_type}')
    
    columns_sql = ', '.join(columns)
    return f'CREATE TABLE "{table_name}" ({columns_sql})'


def _infer_column_type(series: pd.Series) -> str:
    # 移除空值進行分析
    non_null_series = series.dropna()
    
    if non_null_series.empty:
        return 'TEXT'
    
    # 數值類型推斷
    if series.dtype in ['int64', 'int32', 'int16', 'int8']:
        return 'BIGINT'
    elif series.dtype in ['float64', 'float32']:
        return 'DOUBLE PRECISION'
    elif series.dtype == 'bool':
        return 'BOOLEAN'
    elif pd.api.types.is_datetime64_any_dtype(series):
        return 'TIMESTAMP'
    
    # 字串類型推斷
    if series.dtype == 'object':
        # 檢查是否所有值都是字串
        str_values = non_null_series.astype(str)
        max_length = str_values.str.len().max()
        
        # 根據最大長度決定類型
        if max_length <= 50:
            return 'VARCHAR(100)'  # 給一些緩衝空間
        elif max_length <= 200:
            return 'VARCHAR(500)'  # 給一些緩衝空間
        elif max_length <= 1000:
            return 'VARCHAR(2000)' # 給一些緩衝空間
        else:
            return 'TEXT'  # 長文本使用 TEXT 類型
    
    # 預設使用 TEXT
    return 'TEXT'


def _insert_dataframe_to_table(cursor, df: pd.DataFrame, table_name: str):
    if df.empty:
        return
    
    # 準備插入語句
    columns = [f'"{col}"' for col in df.columns]
    placeholders = ['%s'] * len(df.columns)
    expected_col_count = len(df.columns)
    
    insert_sql = f"""
        INSERT INTO "{table_name}" ({', '.join(columns)}) 
        VALUES ({', '.join(placeholders)})
    """
    
    # 批量插入資料
    values = []
    for idx, row in df.iterrows():
        row_values = []
        
        # 確保每行都有正確數量的欄位
        for col in df.columns:
            val = row.get(col)  # 使用 get 方法避免 KeyError
            if pd.isna(val):
                row_values.append(None)
            else:
                str_val = str(val)
                # 安全截斷：如果字串太長，截斷到合理長度
                if len(str_val) > 10000:  # 超過 10000 字元的截斷
                    str_val = str_val[:9997] + "..."
                row_values.append(str_val)
        
        # 驗證欄位數量
        if len(row_values) != expected_col_count:
            print(f"第 {idx+1} 行欄位數量不符 (期望: {expected_col_count}, 實際: {len(row_values)})，跳過")
            continue
            
        values.append(tuple(row_values))
    
    if not values:
        print("沒有有效的資料行可插入")
        return
    
    try:
        cursor.executemany(insert_sql, values)
    except Exception as e:
        # 如果批量插入失敗，嘗試逐行插入以找出問題行
        print(f"批量插入失敗，嘗試逐行插入: {str(e)}")
        success_count = 0
        for i, value_tuple in enumerate(values):
            try:
                # 再次驗證 tuple 長度
                if len(value_tuple) != expected_col_count:
                    print(f"第 {i+1} 行 tuple 長度不符 (期望: {expected_col_count}, 實際: {len(value_tuple)})，跳過")
                    continue
                    
                cursor.execute(insert_sql, value_tuple)
                success_count += 1
            except Exception as row_error:
                print(f"第 {i+1} 行插入失敗，跳過: {str(row_error)}")
                continue
        
        if success_count > 0:
            print(f"成功插入 {success_count}/{len(values)} 行資料")


def _check_database_exists(category: str):

    try:
        # 連到預設 postgres 資料庫
        db_config = settings.DATABASES['default']
        conn = psycopg2.connect(
            host=db_config['HOST'],
            port=db_config['PORT'],
            database=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        db_name = ASSOCIATED_CATEGORIES_DATABASE_NAME[category]
        cursor.execute(
            psycopg2.sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"),
            [db_name]
        )
        exists = cursor.fetchone() is not None

        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            cursor.execute(psycopg2.sql.SQL("CREATE DATABASE {}").format(
                psycopg2.sql.Identifier(db_name)
            ))
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error checking or creating database '{db_name}': {e}")

