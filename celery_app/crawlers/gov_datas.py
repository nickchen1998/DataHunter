import io
import os
import hashlib
import requests
import pandas as pd
from utils.mongodb import get_mongo_database
from pymongo.collection import Collection
from gridfs import GridFS
from gov_datas.models import Dataset

# 下載資料並讀取為 DataFrame
url = "https://data.gov.tw/api/front/dataset/export?format=csv"
content = requests.get(url).content
df = pd.read_csv(io.StringIO(content.decode('utf-8')))

# 篩選「服務分類」為「投資理財」的項目
filtered_df = df[
    (df['服務分類'] == '投資理財') &
    (df['檔案格式'].str.contains('CSV', case=False, na=False))
    ]

with get_mongo_database() as database:
    collection: Collection = database["datasets"]
    file_collection: Collection = database["files"]

    for data in filtered_df.itertuples():
        # 使用 Dataset 模型來驗證和準備資料
        dataset = Dataset(
            dataset_id=data.資料集識別碼,
            url=f"https://data.gov.tw/dataset/{data.資料集識別碼}",
            name=data.資料集名稱,
            category=data.服務分類,
            description=data.資料集描述,
            columns=data.主要欄位說明.split(';'),
            department=data.提供機關,
            update_frequency=data.更新頻率,
            license=data.授權方式,
            price=data.計費方式,
            contact_person=data.提供機關聯絡人姓名,
            contact_phone=data.提供機關聯絡人電話,
            upload_date=data.上架日期,
            update_date=data.詮釋資料更新時間,
        )

        # 更新或插入到 MongoDB
        collection.update_one(
            {"dataset_id": dataset.dataset_id},
            {"$set": dataset.dict(by_alias=True)},  # 使用 dict(by_alias=True) 遵循模型中的欄位別名
            upsert=True
        )

        # 獲取插入或更新後的資料
        dataset_in_db = Dataset(**collection.find_one({"dataset_id": dataset.dataset_id}))

        for file_format, download_url, encoding in zip(
                data.檔案格式.split(';'),
                data.資料下載網址.split(';'),
                data.編碼格式.split(';')
        ):
            if file_format.lower() == "csv":
                # 發送請求取得檔案內容
                try:
                    response = requests.get(download_url, verify=False)
                except Exception as e:
                    print(f"Failed to download {download_url}: {e}")
                    continue

                content = response.content
                content_md5 = hashlib.md5(content).hexdigest()
                if file_collection.find_one({"content_md5": content_md5}):
                    continue

                # 嘗試從 Content-Disposition 標頭中提取檔案名稱
                if 'Content-Disposition' in response.headers:
                    content_disposition = response.headers['Content-Disposition']
                    filename = content_disposition.split("filename=")[-1].strip('"')
                else:
                    # 若 Content-Disposition 無法取得，從 URL 提取檔案名稱
                    filename = os.path.basename(download_url)
                    if not filename or "?" in filename:  # 若無效名稱則給預設值
                        filename = f"dataset_{dataset_in_db.dataset_id}.csv"

                gridfs = GridFS(database)
                gridfs_id = gridfs.put(content)

                # 整合資訊到 dataset_file
                dataset_file = {
                    "format": file_format.lower(),
                    "download_url": download_url,
                    "filename": filename,  # 新增檔案名稱
                    "encoding": encoding,
                    "dataset_id": dataset_in_db.dataset_id,
                    "category": data.服務分類,
                    "content_md5": content_md5,
                    "gridfs_id": gridfs_id,
                }
                file_collection.insert_one(dataset_file)
