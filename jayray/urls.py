# project/urls.py

from django.contrib import admin
from django.urls import path, include
# 👇 FIX: Import the RedirectView class
from django.views.generic import RedirectView 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This line uses the RedirectView we just imported
    path('', RedirectView.as_view(url='/content/', permanent=True)), 

    # Wire up the Content Recorder app at the /content/ base path
    path('content/', include('content_recorder.urls', namespace='content_recorder')), 
    
    
]