# content_recorder/urls.py

from django.urls import path
from .views import ( 
    ContentListView, 
    ContentRecordView, 
    ContentDetailView,
    ContentUpdateView, 
    ContentTrashView,
    # 1. ADD THESE TWO NEW VIEWS:
    ScriptControlsView,
    ScriptGenerationActionView,
    ContentTrashView, # Must match the view name in views.py
)

app_name = 'content_recorder'

urlpatterns = [
    # FIX: Changed path('list/', ...) to path('', ...) so that /content/ resolves to the list view.
    path('', ContentListView.as_view(), name='list'),
    
    # Main Paths
    path('record/', ContentRecordView.as_view(), name='record'),
    path('detail/<int:pk>/', ContentDetailView.as_view(), name='detail'),
    

    # Action Paths
    path('edit/<int:pk>/', ContentUpdateView.as_view(), name='edit'), 
    path('delete/<int:pk>/', ContentTrashView.as_view(), name='delete'),

    # 2. ADD THE TWO NEW PATHS (The names here fix the 'NoReverseMatch' error)
    path('detail/<int:pk>/script/controls/', ScriptControlsView.as_view(), name='script_controls'),
    path('detail/<int:pk>/script/generate/', ScriptGenerationActionView.as_view(), name='generate_script_action'),
]
