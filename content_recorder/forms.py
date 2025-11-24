# content_recorder/forms.py

from django import forms
from .models import ContentIdea

class ContentIdeaForm(forms.ModelForm):
    class Meta:
        model = ContentIdea
        # Include all editable fields
        fields = ['idea_name', 'raw_content', 'status', 'primary_image'] 
        
        widgets = {
            # Use a Textarea for raw_content
            'raw_content': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Paste your content here...'}),
            'idea_name': forms.TextInput(attrs={'placeholder': 'Idea Title (Optional, will auto-fill if blank)'}),
        }

    # CRITICAL FIX: Ensure image field is NOT required for UpdateView
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['primary_image'].required = False