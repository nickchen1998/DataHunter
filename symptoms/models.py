from django.db import models


# Create your models here.
class Symptom(models.Model):
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.id
