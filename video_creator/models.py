
from django.db import models

class Video_creatorItem(models.Model):
    name = models.CharField(max_length=200, default='New Item in Video_creator')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = f"Video_creator Items"
