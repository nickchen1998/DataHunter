import io
import os
import hashlib
import requests
import pandas as pd
import json
import xml.etree.ElementTree as ET
from utils.mongodb import get_mongo_database
from gridfs import GridFS
from gov_datas.models import Dataset, File
from DataHunter.celery import app
from langchain_openai import OpenAIEmbeddings


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
                    'upload_time': row.上架日期 if pd.notna(row.上架日期) else None,
                    'update_time': row.詮釋資料更新時間 if pd.notna(row.詮釋資料更新時間) else None,
                }
            )

            print(f"{'創建' if created else '更新'} 資料集: {dataset.name}")
            # process_dataset_files.delay(row.to_dict(), dataset.id)
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

        if File.objects.filter(content_md5=df_md5).exists():
            print(f"內容已存在於資料庫，跳過: {download_url}")
            continue

        try:
            seen_md5.add(df_md5)
            filename = _extract_filename(response, download_url, dataset.dataset_id)
            _save_file(dataset, df, download_url, file_format, df_md5, filename)
            print(f"成功處理檔案: {filename}")
        except Exception as e:
            print(f"儲存檔案失敗 {download_url}: {str(e)}")


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


def _save_file(dataset, df, download_url, file_format, content_md5, filename):
    csv_content = df.to_csv(index=False)
    
    with get_mongo_database() as database:
        gridfs = GridFS(database)
        gridfs_id = gridfs.put(csv_content.encode('utf-8'))

    File.objects.create(
        dataset=dataset,
        original_download_url=download_url,
        filename=filename,
        encoding='utf-8',
        original_formats=file_format,
        content_md5=content_md5,
        gridfs_id=str(gridfs_id)
    )


def _extract_filename(response, download_url, dataset_id):
    if 'Content-Disposition' in response.headers:
        content_disposition = response.headers['Content-Disposition']
        if 'filename=' in content_disposition:
            return content_disposition.split("filename=")[-1].strip('"')
    
    filename = os.path.basename(download_url.split('?')[0])
    if not filename or not filename.endswith('.csv'):
        filename = f"dataset_{dataset_id}.csv"
    
    return filename


def _get_dataframe_md5(df: pd.DataFrame) -> str:
    df_copy = df.copy().astype(str)
    df_copy = df_copy[sorted(df_copy.columns)]
    df_copy = df_copy.sort_values(by=sorted(df_copy.columns)).reset_index(drop=True)
    
    content_str = df_copy.to_csv(index=False)
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()
