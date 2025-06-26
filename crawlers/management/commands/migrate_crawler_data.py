from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.apps import apps


class Command(BaseCommand):
    help = '將 gov_datas 和 symptoms 應用的資料遷移到 crawlers 應用'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='執行模擬運行，不實際修改資料庫',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制執行，即使目標表已有資料',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('執行模擬運行模式...'))

        # 檢查是否已經有資料
        if not force and not dry_run:
            Dataset = apps.get_model('crawlers', 'Dataset')
            Symptom = apps.get_model('crawlers', 'Symptom')
            
            if Dataset.objects.exists() or Symptom.objects.exists():
                self.stdout.write(
                    self.style.ERROR(
                        'crawlers 應用中已有資料！請使用 --force 參數強制執行，或使用 --dry-run 查看遷移計劃。'
                    )
                )
                return

        with transaction.atomic():
            try:
                # 遷移 Dataset 資料
                self.migrate_datasets(dry_run)
                
                # 遷移 File 資料
                self.migrate_files(dry_run)
                
                # 遷移 Symptom 資料
                self.migrate_symptoms(dry_run)
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS('模擬運行完成！上述操作將在實際執行時進行。')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('資料遷移完成！')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'遷移過程中發生錯誤: {e}')
                )
                raise

    def migrate_datasets(self, dry_run):
        """遷移 Dataset 資料"""
        with connection.cursor() as cursor:
            # 檢查源表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'gov_datas_dataset'
                );
            """)
            
            if not cursor.fetchone()[0]:
                self.stdout.write('gov_datas_dataset 表不存在，跳過 Dataset 遷移')
                return

            # 獲取資料數量
            cursor.execute("SELECT COUNT(*) FROM gov_datas_dataset")
            count = cursor.fetchone()[0]
            
            self.stdout.write(f'準備遷移 {count} 筆 Dataset 資料...')
            
            if not dry_run:
                # 執行資料遷移
                cursor.execute("""
                    INSERT INTO crawlers_dataset (
                        dataset_id, url, name, category, description, department,
                        update_frequency, license, price, contact_person, contact_phone,
                        upload_time, update_time, description_embeddings
                    )
                    SELECT 
                        dataset_id, url, name, category, description, department,
                        update_frequency, license, price, contact_person, contact_phone,
                        upload_time, update_time, description_embeddings
                    FROM gov_datas_dataset
                    ON CONFLICT (dataset_id) DO NOTHING;
                """)
                
                migrated = cursor.rowcount
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 已遷移 {migrated} 筆 Dataset 資料')
                )

    def migrate_files(self, dry_run):
        """遷移 File 資料"""
        with connection.cursor() as cursor:
            # 檢查源表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'gov_datas_file'
                );
            """)
            
            if not cursor.fetchone()[0]:
                self.stdout.write('gov_datas_file 表不存在，跳過 File 遷移')
                return

            # 獲取資料數量
            cursor.execute("SELECT COUNT(*) FROM gov_datas_file")
            count = cursor.fetchone()[0]
            
            self.stdout.write(f'準備遷移 {count} 筆 File 資料...')
            
            if not dry_run:
                # 執行資料遷移
                cursor.execute("""
                    INSERT INTO crawlers_file (
                        id, dataset_id, original_download_url, original_format, encoding,
                        content_md5, table_name, database_name, column_mapping_list, created_at
                    )
                    SELECT 
                        f.id, f.dataset_id, f.original_download_url, f.original_format, f.encoding,
                        f.content_md5, f.table_name, f.database_name, f.column_mapping_list, f.created_at
                    FROM gov_datas_file f
                    INNER JOIN crawlers_dataset d ON f.dataset_id = d.id
                    ON CONFLICT (content_md5) DO NOTHING;
                """)
                
                migrated = cursor.rowcount
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 已遷移 {migrated} 筆 File 資料')
                )

    def migrate_symptoms(self, dry_run):
        """遷移 Symptom 資料"""
        with connection.cursor() as cursor:
            # 檢查源表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'symptoms_symptom'
                );
            """)
            
            if not cursor.fetchone()[0]:
                self.stdout.write('symptoms_symptom 表不存在，跳過 Symptom 遷移')
                return

            # 獲取資料數量
            cursor.execute("SELECT COUNT(*) FROM symptoms_symptom")
            count = cursor.fetchone()[0]
            
            self.stdout.write(f'準備遷移 {count} 筆 Symptom 資料...')
            
            if not dry_run:
                # 執行資料遷移
                cursor.execute("""
                    INSERT INTO crawlers_symptom (
                        id, subject_id, subject, department, symptom, question, answer,
                        gender, question_time, answer_time, question_embeddings
                    )
                    SELECT 
                        id, subject_id, subject, department, symptom, question, answer,
                        gender, question_time, answer_time, question_embeddings
                    FROM symptoms_symptom
                    ON CONFLICT (id) DO NOTHING;
                """)
                
                migrated = cursor.rowcount
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 已遷移 {migrated} 筆 Symptom 資料')
                )

    def verify_migration(self):
        """驗證遷移結果"""
        Dataset = apps.get_model('crawlers', 'Dataset')
        File = apps.get_model('crawlers', 'File')
        Symptom = apps.get_model('crawlers', 'Symptom')
        
        dataset_count = Dataset.objects.count()
        file_count = File.objects.count()
        symptom_count = Symptom.objects.count()
        
        self.stdout.write('遷移結果驗證:')
        self.stdout.write(f'  Dataset: {dataset_count} 筆')
        self.stdout.write(f'  File: {file_count} 筆')
        self.stdout.write(f'  Symptom: {symptom_count} 筆') 