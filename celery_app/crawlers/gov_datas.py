import io
import os
import hashlib
import requests
import pandas as pd
from utils.mongodb import get_mongo_database
from gridfs import GridFS
from gov_datas.models import Dataset, File
from DataHunter.celery import app


@app.task()
def period_crawl_government_datasets(demo=False):
    url = "https://data.gov.tw/api/front/dataset/export?format=csv"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    csv_df = df[df['檔案格式'].str.contains('CSV', case=False, na=False)]
    categories = csv_df['服務分類'].unique()

    if demo:
        categories = ['投資理財']

    processed_datasets = 0

    for category in categories:
        sub_df = csv_df[csv_df['服務分類'] == category]
        for _, row in sub_df.iterrows():
            dataset, created = Dataset.objects.update_or_create(
                dataset_id=row.資料集識別碼,
                defaults={
                    'url': f"https://data.gov.tw/dataset/{row.資料集識別碼}",
                    'name': row.資料集名稱,
                    'category': row.服務分類,
                    'description': row.資料集描述,
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

    min_length = min(len(file_formats), len(download_urls), len(encodings))

    with get_mongo_database() as database:
        gridfs = GridFS(database)

        for i in range(min_length):
            file_format = file_formats[i].strip()
            download_url = download_urls[i].strip()
            encoding = encodings[i].strip()

            if file_format.lower() != "csv":
                continue

            try:
                response = requests.get(download_url, verify=False, timeout=30)
                response.raise_for_status()

                content = response.content
                content_md5 = hashlib.md5(content).hexdigest()

                if File.objects.filter(content_md5=content_md5).exists():
                    continue

                filename = _extract_filename(response, download_url, dataset.dataset_id)
                gridfs_id = gridfs.put(content)

                File.objects.create(
                    dataset=dataset,
                    original_download_url=download_url,
                    filename=filename,
                    encoding=encoding,
                    format=file_format.lower(),
                    content_md5=content_md5,
                    gridfs_id=str(gridfs_id)
                )

                print(f"成功處理檔案: {filename}")

            except Exception as e:
                print(f"下載檔案失敗 {download_url}: {str(e)}")
                continue


def _extract_filename(response, download_url, dataset_id):
    if 'Content-Disposition' in response.headers:
        content_disposition = response.headers['Content-Disposition']
        if 'filename=' in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')
            return filename
    
    filename = os.path.basename(download_url.split('?')[0])
    if not filename or not filename.endswith('.csv'):
        filename = f"dataset_{dataset_id}.csv"
    
    return filename
