# Generated by Django 5.2 on 2025-04-28 10:40

import django.utils.timezone
import pgvector.django.vector
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('symptoms', '0002_add_pg_vector_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='symptom',
            name='age',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='answer',
            field=models.TextField(default='test'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='answer_time',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='網站上的醫師回答時間。'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='department',
            field=models.CharField(default=django.utils.timezone.now, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='gender',
            field=models.CharField(default='male', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='question',
            field=models.TextField(default='test'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='question_embedding',
            field=pgvector.django.vector.VectorField(
                default=[0.1]*1536,
                dimensions=1536,
                help_text='基於 question 欄位並使用 OpenAI text-embedding-3-small 產生向量。'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='question_time',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='網站上的患者提問時間。'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='subject_id',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='symptom',
            name='symptom',
            field=models.CharField(default='test', max_length=255),
            preserve_default=False,
        ),
    ]
