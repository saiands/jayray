
from django.db import models

class Platform_media_convertorItem(models.Model):
    name = models.CharField(max_length=200, default='New Item in Platform_media_convertor')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = f"Platform_media_convertor Items"
