
from django.db import models

class Script_writerItem(models.Model):
    name = models.CharField(max_length=200, default='New Item in Script_writer')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = f"Script_writer Items"
