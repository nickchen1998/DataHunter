from django.db import models
from pgvector.django import VectorField


# Create your models here.
class Symptom(models.Model):
    id = models.AutoField(primary_key=True)

    subject_id = models.IntegerField()
    department = models.CharField(max_length=255)

    symptom = models.CharField(max_length=255)
    question = models.TextField()
    answer = models.TextField()

    gender = models.CharField(max_length=10)

    question_time = models.DateTimeField(help_text="網站上的患者提問時間。")
    answer_time = models.DateTimeField(help_text="網站上的醫師回答時間。")
    created_at = models.DateTimeField(auto_now_add=True)

    question_embeddings = VectorField(
        dimensions=1536,
        help_text="基於 question 欄位並使用 OpenAI text-embedding-3-small 產生向量。"
    )

    def __str__(self):
        return self.id
