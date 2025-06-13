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
def period_crawl_government_datasets():
    """
    定期爬取政府開放資料平台的資料集（所有 CSV 格式資料）
    """
    crawl_government_datasets()


@app.task()
def crawl_government_datasets(filter_category=None):
    """
    爬取政府開放資料平台的資料集
    
    Args:
        filter_category (str, optional): 篩選的服務分類，如 '投資理財'
    """
    try:
        print("開始爬取政府開放資料...")
        
        # 下載資料並讀取為 DataFrame
        url = "https://data.gov.tw/api/front/dataset/export?format=csv"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        print(f"成功載入 {len(df)} 筆資料集資訊")
        
        # 篩選資料（如果有指定分類）
        if filter_category:
            filtered_df = df[
                (df['服務分類'] == filter_category) &
                (df['檔案格式'].str.contains('CSV', case=False, na=False))
            ]
            print(f"篩選後剩餘 {len(filtered_df)} 筆資料")
        else:
            filtered_df = df[df['檔案格式'].str.contains('CSV', case=False, na=False)]
        
        total_datasets = len(filtered_df)
        processed_datasets = 0
        
        for data in filtered_df.itertuples():
            try:
                # 使用 Django ORM 創建或更新資料集
                dataset, created = Dataset.objects.update_or_create(
                    dataset_id=data.資料集識別碼,
                    defaults={
                        'url': f"https://data.gov.tw/dataset/{data.資料集識別碼}",
                        'name': data.資料集名稱,
                        'category': data.服務分類,
                        'description': data.資料集描述,
                        'columns_description': data.主要欄位說明.split(';') if pd.notna(data.主要欄位說明) else [],
                        'department': data.提供機關,
                        'update_frequency': data.更新頻率,
                        'license': data.授權方式,
                        'price': data.計費方式,
                        'contact_person': data.提供機關聯絡人姓名 if pd.notna(data.提供機關聯絡人姓名) else None,
                        'contact_phone': data.提供機關聯絡人電話 if pd.notna(data.提供機關聯絡人電話) else None,
                        'upload_time': data.上架日期 if pd.notna(data.上架日期) else None,
                        'update_time': data.詮釋資料更新時間 if pd.notna(data.詮釋資料更新時間) else None,
                    }
                )
                
                print(f"{'創建' if created else '更新'} 資料集: {dataset.name}")
                
                # 處理檔案
                _process_dataset_files(data, dataset)
                
                processed_datasets += 1
                
            except Exception as e:
                print(f"處理資料集 {data.資料集識別碼} 時發生錯誤: {str(e)}")
                continue
        
        print(f"爬取完成！共處理 {processed_datasets} 個資料集")
        return {
            'status': 'SUCCESS',
            'processed': processed_datasets,
            'total': total_datasets
        }
        
    except Exception as e:
        print(f"爬取過程發生錯誤: {str(e)}")
        raise e


def _process_dataset_files(data, dataset):
    """處理資料集的檔案"""
    if pd.isna(data.檔案格式) or pd.isna(data.資料下載網址) or pd.isna(data.編碼格式):
        return
    
    file_formats = str(data.檔案格式).split(';')
    download_urls = str(data.資料下載網址).split(';')
    encodings = str(data.編碼格式).split(';')
    
    # 確保所有列表長度一致
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
                # 檢查是否已存在相同的檔案
                if File.objects.filter(
                    dataset=dataset,
                    original_download_url=download_url
                ).exists():
                    print(f"檔案已存在，跳過: {download_url}")
                    continue
                
                # 下載檔案
                response = requests.get(download_url, verify=False, timeout=30)
                response.raise_for_status()
                
                content = response.content
                content_md5 = hashlib.md5(content).hexdigest()
                
                # 檢查是否已有相同內容的檔案
                if File.objects.filter(content_md5=content_md5).exists():
                    print(f"相同內容的檔案已存在，跳過: {download_url}")
                    continue
                
                # 提取檔案名稱
                filename = _extract_filename(response, download_url, dataset.dataset_id)
                
                # 儲存到 GridFS
                gridfs_id = gridfs.put(content)
                
                # 創建檔案記錄
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
    """提取檔案名稱"""
    # 嘗試從 Content-Disposition 標頭中提取檔案名稱
    if 'Content-Disposition' in response.headers:
        content_disposition = response.headers['Content-Disposition']
        if 'filename=' in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')
            return filename
    
    # 從 URL 提取檔案名稱
    filename = os.path.basename(download_url.split('?')[0])
    
    # 如果無法提取有效名稱，使用預設值
    if not filename or not filename.endswith('.csv'):
        filename = f"dataset_{dataset_id}.csv"
    
    return filename
