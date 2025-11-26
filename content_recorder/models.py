from django.db import models
from django.conf import settings

from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage # or S3Storage, etc.

# --- Custom Manager for Soft Delete ---
class ContentIdeaManager(models.Manager):
    """Custom manager to exclude soft-deleted ideas by default."""
    def get_queryset(self):
        # Only return ideas where is_deleted is False
        return super().get_queryset().filter(is_deleted=False)

# --- Models ---
class ContentIdea(models.Model):
    # Status choices (must match your forms/views)
    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft (New Idea)'
        RESEARCH = 'Research', 'Research/Data Gathering'
        SCRIPT = 'Script', 'Script Ready'
        PRODUCTION = 'Production', 'In Production'
        PUBLISHED = 'Published', 'Published'
        ARCHIVED = 'Archived', 'Archived'
        DUPLICATE = 'Duplicate', 'Duplicate/Rejected'

    # Primary Key - using a standard AutoField for simplicity unless UUID is necessary
    content_id = models.AutoField(primary_key=True) 
    
    idea_name = models.CharField(max_length=255, verbose_name="Idea Title", blank=True, null=True)
    raw_content = models.TextField(verbose_name="Raw Input Content")
    
    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
        verbose_name="Workflow Status"
    )
    
    primary_image = models.ImageField(
        upload_to='idea_images/', 
        verbose_name="Primary Image/Thumbnail", 
        blank=True, 
        null=True
    )
    
    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = ContentIdeaManager() # Default manager (excludes deleted)
    all_objects = models.Manager()  # Manager that includes ALL objects (for admin/trash recovery)

    def __str__(self):
        return f"{self.content_id}: {self.idea_name or self.raw_content[:30]}"
    
    class Meta:
        verbose_name = "Content Idea"
        verbose_name_plural = "Content Ideas"


class ContentSource(models.Model):
    class SourceType(models.TextChoices):
        TEXT = 'Text', 'Pasted Text'
        FILE = 'File', 'File Upload'
        URL = 'URL', 'Web Link/URL'

    idea = models.ForeignKey(ContentIdea, on_delete=models.CASCADE, related_name='sources')
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    source_data = models.TextField() # Can hold file name, URL, or brief description
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Source for {self.idea.idea_name}: {self.source_type}"

class IdeaLog(models.Model):
    idea = models.ForeignKey(ContentIdea, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.idea.idea_name} at {self.timestamp}"


# ==================================
# NEW MODEL FOR SCRIPT BREAKDOWN DATA
# ==================================
class ScriptBreakdown(models.Model):
    """
    Stores the structured JSON output from the LLM for a content idea.
    Uses OneToOneField since one idea should only have one script breakdown at a time.
    """
    idea = models.OneToOneField(
        'ContentIdea', 
        on_delete=models.CASCADE, 
        related_name='breakdown'
    )
    
    # Store the actual structured script output (the scenes array, etc.)
    breakdown_data = models.JSONField() 
    
    # Store the prompt used to generate this specific version for auditing
    prompt_used = models.CharField(max_length=50, verbose_name="LLM Prompt Version")
    
    # Store additional constraints used
    target_platform = models.CharField(max_length=50)
    global_mood = models.CharField(max_length=50)
    target_audience = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Breakdown for {self.idea.idea_name} ({self.prompt_used})"
    
    # Define storage location for images (adjust as needed for production)
fs = FileSystemStorage(location='/var/www/media/storyboard_trash')

class SceneImage(models.Model):
    """
    Stores metadata for each generated storyboard image, supporting soft-delete.
    """
    # Link to the main idea
    idea = models.ForeignKey(
        'ContentIdea', 
        on_delete=models.CASCADE,
        related_name='scene_images', 
        help_text="The core idea this image belongs to."
    )
    
    # Link to the scene data (using ID or index from the JSON breakdown)
    scene_index = models.IntegerField(help_text="Index or ID of the scene in the ScriptBreakdown.")
    
    # Image file storage
    image_file = models.ImageField(upload_to='storyboards/%Y/%m/', help_text="The generated image file.")
    
    # Prompt used for this specific generation
    full_prompt = models.TextField(help_text="The exact prompt used to generate this image.")
    
    # Generation parameters for consistency/reproducibility
    camera_angle = models.CharField(max_length=100, help_text="e.g., Wide shot, Close up.")
    style_prompt = models.CharField(max_length=255, help_text="e.g., Film noir aesthetic.")
    negative_prompt = models.TextField(help_text="The negative prompt used.")
    
    # Soft Delete Implementation
    is_deleted = models.BooleanField(default=False, help_text="Set to True for soft deletion.")
    
    # File movement for soft delete
    trash_file = models.FileField(
        storage=fs, 
        upload_to='trash/', 
        null=True, 
        blank=True,
        help_text="Storage location if image is soft-deleted."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for Idea {self.idea.pk}, Scene {self.scene_index}"

    def soft_delete(self):
        """Moves the file to trash and sets the is_deleted flag."""
        if not self.is_deleted:
            # 1. Save file to the trash location
            with self.image_file.open('rb') as f:
                self.trash_file.save(f"deleted_{self.image_file.name}", f)

            # 2. Delete the original file
            self.image_file.delete(save=False)
            
            # 3. Mark as deleted
            self.is_deleted = True
            self.save()

# Note: Remember to run migrations after adding this model!