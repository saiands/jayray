
from django.db import models

class Image_generatorItem(models.Model):
    name = models.CharField(max_length=200, default='New Item in Image_generator')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = f"Image_generator Items"
