from django.contrib import admin
from .models import ContentIdea, IdeaLog # Import IdeaLog for logging the restore action

# --- Custom Admin Action ---
@admin.action(description='Restore selected ideas from Trash')
def restore_ideas(modeladmin, request, queryset):
    """Sets is_deleted to False for selected items and logs the action."""
    
    # 1. Perform the restoration (setting is_deleted=False)
    restored_count = queryset.update(is_deleted=False)
    
    # 2. Log the action for each restored item
    for idea in queryset:
        IdeaLog.objects.create(
            idea=idea,
            user=request.user,
            action=f"Idea restored from Trash via Admin"
        )
        
    modeladmin.message_user(
        request,
        f"{restored_count} idea(s) successfully restored from trash.",
        level='success'
    )


# --- Custom Model Admin ---
class ContentIdeaAdmin(admin.ModelAdmin):
    # Display the essential fields, including the soft-delete status
    list_display = (
        'content_id', 
        'idea_name', 
        'status', 
        'is_deleted', # CRITICAL: Allows viewing which ideas are trashed
        'created_at', 
        'updated_at'
    )
    
    # Allow filtering by status and soft-delete status
    list_filter = ('status', 'is_deleted', 'created_at')
    search_fields = ('idea_name', 'raw_content')
    
    # CRITICAL: Override queryset to use the 'all_objects' manager, showing ALL items
    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

    # Add the custom action
    actions = [restore_ideas]


# Register the model with the custom Admin class
admin.site.register(ContentIdea, ContentIdeaAdmin)