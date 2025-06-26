from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Limit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    chat_limit_per_day = models.IntegerField(default=500)
    private_source_limit = models.IntegerField(default=5)
    file_limit_per_source = models.IntegerField(default=30)
    
    def __str__(self):
        return f"{self.user.username} - Limit"