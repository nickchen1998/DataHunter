# Generated by Django 5.2.3 on 2025-06-14 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gov_datas', '0010_remove_file_column_count_remove_file_row_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='database_name',
            field=models.CharField(default='InvestmentAndFinancialManagementGovData', help_text='在 GovData 資料庫中的資料庫名稱', max_length=255, verbose_name='對應資料庫名稱'),
        ),
    ]
