
from django.contrib import admin
from . import models # CORRECTED: Use relative import for the models file

# Register your models here.
admin.site.register(models.Image_generatorItem)
