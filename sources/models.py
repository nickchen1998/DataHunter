from django.db import models


class SourceFileFormat(models.TextChoices):
    PDF = 'pdf'
    DOCX = 'docx'
    TXT = 'txt'
    CSV = 'csv'
    XLS = 'xls'
    JSON = 'json'

# Create your models here.
class Source(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SourceFile(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    file = models.FileField(upload_to='source_files/')
    format = models.CharField(max_length=10, choices=SourceFileFormat.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.name


class SourceFileChunk(models.Model):
    source_file = models.ForeignKey(SourceFile, on_delete=models.CASCADE)
    chunk = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.source_file.file.name