from django.contrib import admin
from .models import (
    ContentIdea,
    ScriptBreakdown,
    SceneImage,
    ContentSource,
    IdeaLog
)

# --- Import Prompt House Models ---
# CRITICAL: Imports the Prompt House models, including the new DynamicPromptField
from prompt_house.models import PromptRule, PromptStep, PromptTemplate, DynamicPromptField


# --- Inlines (For showing related data on the ContentIdea admin page) ---
class ScriptBreakdownInline(admin.StackedInline):
    model = ScriptBreakdown
    extra = 0
    max_num = 1
    fields = ('prompt_used', 'global_mood', 'target_platform', 'target_audience', 'breakdown_data')
    readonly_fields = ('prompt_used',)

class SceneImageInline(admin.TabularInline):
    model = SceneImage
    extra = 0
    # Add a custom method to display the image thumbnail in the admin
    readonly_fields = ('scene_index', 'full_prompt', 'created_at',)
    fields = ('scene_index', 'full_prompt', 'created_at', 'is_deleted',)


# --- Dynamic Field Inline (For PromptTemplate) ---
class DynamicPromptFieldInline(admin.TabularInline):
    """Allows adding/editing dynamic key-value pairs directly on the template page."""
    model = DynamicPromptField
    extra = 1
    fields = ('order', 'label_key', 'field_value',)


# --- Custom Admin Actions ---
@admin.action(description='Soft-delete selected content ideas (Move to Trash)')
def soft_delete_ideas(modeladmin, request, queryset):
    """Sets is_deleted to True for selected items and logs the action."""
    for idea in queryset:
        idea.is_deleted = True
        idea.save()
        IdeaLog.objects.create(
            idea=idea,
            user=request.user,
            action="Soft-deleted content idea (Moved to Trash)."
        )
    modeladmin.message_user(request, f"{queryset.count()} ideas soft-deleted.")


@admin.action(description='Restore selected content ideas from Trash')
def restore_ideas(modeladmin, request, queryset):
    """Sets is_deleted to False for selected items and logs the action."""
    restored_count = queryset.update(is_deleted=False)

    # Log the action for each restored item
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


# --- ContentIdea Admin Registration ---
@admin.register(ContentIdea)
class ContentIdeaAdmin(admin.ModelAdmin):
    # Display the essential fields, including the soft-delete status and Prompt House link
    list_display = (
        'content_id',
        'title',
        'status',
        'prompt_template', # <-- PROMPT HOUSE LINK
        'is_deleted',
        'created_at'
    )

    # Allow filtering by status, soft-delete status, and template
    list_filter = ('status', 'is_deleted', 'prompt_template')
    search_fields = ('title', 'raw_content', 'content_id')

    # CRITICAL: Override queryset to use the 'all_objects' manager, showing ALL items (including trashed)
    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

    # Add the custom actions
    actions = [soft_delete_ideas, restore_ideas]

    fieldsets = (
        (None, {
            'fields': ('title', 'idea_name', 'raw_content', 'status', 'primary_image'),
        }),
        ('Prompt House & Generation', {
            'fields': ('prompt_template',), # <-- PROMPT HOUSE FIELD
            'description': 'Select the structured prompt template to guide the LLM generation.'
        }),
        ('Audit & Metadata', {
            'fields': ('is_deleted',),
            'classes': ('collapse',),
        }),
    )

    inlines = [
        ScriptBreakdownInline,
        # SceneImageInline,
    ]


@admin.register(ScriptBreakdown)
class ScriptBreakdownAdmin(admin.ModelAdmin):
    list_display = ('idea', 'prompt_used', 'target_platform', 'global_mood', 'created_at')
    search_fields = ('idea__title', 'breakdown_data')
    readonly_fields = ('idea', 'prompt_used', 'created_at', 'breakdown_data')

@admin.register(SceneImage)
class SceneImageAdmin(admin.ModelAdmin):
    list_display = ('idea', 'scene_index', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('idea__title', 'full_prompt')
    readonly_fields = ('idea', 'full_prompt', 'negative_prompt', 'trash_file', 'created_at')

@admin.register(ContentSource)
class ContentSourceAdmin(admin.ModelAdmin):
    list_display = ('idea', 'source_type', 'description', 'created_at')
    list_filter = ('source_type',)
    search_fields = ('idea__title', 'source_data')

@admin.register(IdeaLog)
class IdeaLogAdmin(admin.ModelAdmin):
    list_display = ('idea', 'user', 'action', 'timestamp')
    list_filter = ('user',)
    search_fields = ('idea__title', 'action')
    readonly_fields = ('idea', 'user', 'action', 'timestamp')

# --- Prompt House Admin Registrations ---

@admin.register(PromptRule)
class PromptRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'id')
    list_filter = ('is_active',)
    search_fields = ('name', 'text')

@admin.register(PromptStep)
class PromptStepAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'id')
    list_filter = ('is_active',)
    search_fields = ('name', 'text')

@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_text', 'description')
    search_fields = ('name', 'role_text', 'task_text')
    # filter_horizontal is great for ManyToMany fields in the admin interface
    filter_horizontal = ('rules', 'reasoning_steps')

    fieldsets = (
        (None, {
            'fields': ('name', 'description'),
        }),
        ('Core Prompt Sections (Standard Labels)', {
            'fields': ('role_text', 'task_text', 'context_text', 'output_format', 'stop_conditions'),
            'description': 'These are the standard, non-customizable sections of the prompt.',
        }),
        ('Reusable Components (Checklists)',
            {'fields': ('rules', 'reasoning_steps')}
        ),
    )

    # ADD THE DYNAMIC FIELD INLINE
    inlines = [DynamicPromptFieldInline]