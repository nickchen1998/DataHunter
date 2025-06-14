# Generated by Django 5.2.3 on 2025-06-14 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gov_datas', '0006_change_time_fields_to_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='update_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='詮釋資料更新時間'),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='upload_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='上架日期'),
        ),
    ]
