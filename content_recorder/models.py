from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from prompt_house.models import PromptTemplate 

# --- Custom Manager for Soft Delete ---
class ContentIdeaManager(models.Manager):
    """Custom manager to exclude soft-deleted ideas by default."""
    def get_queryset(self):
        # Only return ideas where is_deleted is False
        return super().get_queryset().filter(is_deleted=False)

# Define storage location for deleted images (adjust as needed for production)
fs = FileSystemStorage(location='/var/www/media/storyboard_trash')

# --- Main Models ---

class ContentIdea(models.Model):
    """
    Stores the core idea, links to the Script Breakdown, and Prompt Template.
    """
    # Status choices
    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft (New Idea)'
        RESEARCH = 'Research', 'Research/Data Gathering'
        SCRIPT = 'Script', 'Script Ready'
        PRODUCTION = 'Production', 'In Production'
        PUBLISHED = 'Published', 'Published'
        ARCHIVED = 'Archived', 'Archived'
        DUPLICATE = 'Duplicate', 'Duplicate/Rejected'

    # Primary Key
    content_id = models.AutoField(primary_key=True) 
    
    # Core Content Fields
    title = models.CharField(max_length=255, verbose_name="Idea Title", help_text="The primary name for the content.")
    idea_name = models.CharField(max_length=255, verbose_name="Idea Title (Secondary)", blank=True, null=True) 
    raw_content = models.TextField(verbose_name="Raw Input Content")
    
    # Workflow & Visual Fields
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
    
    # --- PROMPT HOUSE INTEGRATION ---
    prompt_template = models.ForeignKey(
        PromptTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="The structured template to use for generating the Script Breakdown."
    )
    
    # Managers & Soft Delete
    is_deleted = models.BooleanField(default=False)
    objects = ContentIdeaManager()  # Default manager (excludes deleted)
    all_objects = models.Manager()  # Manager that includes ALL objects
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.content_id}: {self.title or self.idea_name or self.raw_content[:30]}"
    
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
        return f"Source for {self.idea.title}: {self.source_type}"

class IdeaLog(models.Model):
    idea = models.ForeignKey(ContentIdea, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.idea.title} at {self.timestamp}"

class ScriptBreakdown(models.Model):
    """
    Stores the structured JSON output from the LLM for a content idea.
    """
    idea = models.OneToOneField(
        ContentIdea, 
        on_delete=models.CASCADE, 
        related_name='breakdown'
    )
    
    breakdown_data = models.JSONField() 
    prompt_used = models.CharField(max_length=50, verbose_name="LLM Prompt Version")
    target_platform = models.CharField(max_length=50)
    global_mood = models.CharField(max_length=50)
    target_audience = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Breakdown for {self.idea.title} ({self.prompt_used})"
    

class SceneImage(models.Model):
    """
    Stores metadata for each generated storyboard image, supporting soft-delete.
    """
    idea = models.ForeignKey(
        ContentIdea, 
        on_delete=models.CASCADE,
        related_name='scene_images', 
        help_text="The core idea this image belongs to."
    )
    
    scene_index = models.IntegerField(help_text="Index or ID of the scene in the ScriptBreakdown.")
    image_file = models.ImageField(upload_to='storyboards/%Y/%m/', help_text="The generated image file.")
    full_prompt = models.TextField(help_text="The exact prompt used to generate this image.")
    camera_angle = models.CharField(max_length=100, help_text="e.g., Wide shot, Close up.")
    style_prompt = models.CharField(max_length=255, help_text="e.g., Film noir aesthetic.")
    negative_prompt = models.TextField(help_text="The negative prompt used.")
    
    is_deleted = models.BooleanField(default=False, help_text="Set to True for soft deletion.")
    
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
            if self.image_file:
                with self.image_file.open('rb') as f:
                    self.trash_file.save(f"deleted_{self.image_file.name}", f)

                self.image_file.delete(save=False)
            
            self.is_deleted = True
            self.save()