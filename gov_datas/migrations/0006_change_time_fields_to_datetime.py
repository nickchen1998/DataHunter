# Generated by Django 5.2.3 on 2025-06-14 08:25

from django.db import migrations, models
from datetime import datetime


def convert_time_strings_to_datetime(apps, schema_editor):
    """
    將現有的時間字串轉換為 datetime 物件
    """
    Dataset = apps.get_model('gov_datas', 'Dataset')
    
    def parse_datetime_string(date_string):
        """解析時間字串並轉換為 datetime 物件"""
        if not date_string:
            return None
        
        try:
            date_string = str(date_string).strip()
            
            # 嘗試解析完整的日期時間格式
            if len(date_string) > 10:  # 包含時間部分
                return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            else:  # 只有日期部分
                return datetime.strptime(date_string, '%Y-%m-%d')
        except ValueError:
            try:
                # 嘗試其他可能的格式
                return datetime.strptime(date_string, '%Y/%m/%d %H:%M:%S')
            except ValueError:
                try:
                    return datetime.strptime(date_string, '%Y/%m/%d')
                except ValueError:
                    print(f"無法解析時間格式: {date_string}")
                    return None
    
    # 先添加新的 datetime 欄位
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            ALTER TABLE gov_datas_dataset 
            ADD COLUMN upload_time_new TIMESTAMP WITH TIME ZONE NULL,
            ADD COLUMN update_time_new TIMESTAMP WITH TIME ZONE NULL;
        """)
    
    # 轉換現有資料
    for dataset in Dataset.objects.all():
        upload_time_dt = parse_datetime_string(dataset.upload_time)
        update_time_dt = parse_datetime_string(dataset.update_time)
        
        # 直接使用 SQL 更新以避免模型驗證問題
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE gov_datas_dataset 
                SET upload_time_new = %s, update_time_new = %s 
                WHERE id = %s
            """, [upload_time_dt, update_time_dt, dataset.id])
    
    # 刪除舊欄位並重命名新欄位
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE gov_datas_dataset DROP COLUMN upload_time;")
        cursor.execute("ALTER TABLE gov_datas_dataset DROP COLUMN update_time;")
        cursor.execute("ALTER TABLE gov_datas_dataset RENAME COLUMN upload_time_new TO upload_time;")
        cursor.execute("ALTER TABLE gov_datas_dataset RENAME COLUMN update_time_new TO update_time;")


def reverse_convert_datetime_to_strings(apps, schema_editor):
    """
    反向操作：將 datetime 轉換回字串
    """
    Dataset = apps.get_model('gov_datas', 'Dataset')
    
    # 先添加新的字串欄位
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            ALTER TABLE gov_datas_dataset 
            ADD COLUMN upload_time_new VARCHAR(50) NULL,
            ADD COLUMN update_time_new VARCHAR(50) NULL;
        """)
    
    # 轉換現有資料
    for dataset in Dataset.objects.all():
        upload_time_str = dataset.upload_time.strftime('%Y-%m-%d %H:%M:%S') if dataset.upload_time else None
        update_time_str = dataset.update_time.strftime('%Y-%m-%d %H:%M:%S') if dataset.update_time else None
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE gov_datas_dataset 
                SET upload_time_new = %s, update_time_new = %s 
                WHERE id = %s
            """, [upload_time_str, update_time_str, dataset.id])
    
    # 刪除舊欄位並重命名新欄位
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE gov_datas_dataset DROP COLUMN upload_time;")
        cursor.execute("ALTER TABLE gov_datas_dataset DROP COLUMN update_time;")
        cursor.execute("ALTER TABLE gov_datas_dataset RENAME COLUMN upload_time_new TO upload_time;")
        cursor.execute("ALTER TABLE gov_datas_dataset RENAME COLUMN update_time_new TO update_time;")


class Migration(migrations.Migration):

    dependencies = [
        ('gov_datas', '0005_alter_dataset_category'),
    ]

    operations = [
        migrations.RunPython(
            convert_time_strings_to_datetime,
            reverse_convert_datetime_to_strings
        ),
    ] 