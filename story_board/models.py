
from django.db import models

class Story_boardItem(models.Model):
    name = models.CharField(max_length=200, default='New Item in Story_board')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = f"Story_board Items"
