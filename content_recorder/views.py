from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView
from django.db import transaction 
from django.conf import settings
import requests
import json 
import os 
from django.db import IntegrityError # Import IntegrityError for robust saving

from .models import ContentIdea, ContentSource, IdeaLog, ScriptBreakdown
from .forms import ContentIdeaForm 

# External Libraries for File Parsing
try:
    from docx import Document
except ImportError:
    Document = None
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


# =========================================================================
# --- LLM Prompt Templates and Helper Function ---
# =========================================================================

# NOTE: Variables to be formatted MUST use single braces: {...}
# Literal braces (for JSON instruction) MUST use double braces: {{...}}

PROMPT_V1 = """
**Role:** Senior Content Strategist and Structural Analyst.

**Task:** Deconstruct the provided `RAW CONTENT` into a logically sequenced **scene-by-scene structural outline** that serves as the primary blueprint for a human scriptwriter.

**Context:**
Analyze the content idea specifically for a **{target_platform}** video, referencing the core inputs:
1. IDEA NAME: {idea_name}
2. GLOBAL MOOD: {global_mood}
3. RAW CONTENT: 
---
{raw_content}
---

**Reasoning:** The breakdown must serve as the primary blueprint for a human writer, ensuring content coverage and logical flow. The breakdown must divide the raw content into discrete, narrative scenes, assigning a realistic estimated word count for pacing and suggested visual direction.

**Output Format:** Strict **JSON object** adhering to the required `ScriptBreakdown` schema. The JSON structure should look like: {{"script_breakdown": {{"scenes": [...]}}}}

**Stop Conditions:** End output immediately after the closing }} of the JSON object. Do not include any introductory, concluding, or explanatory text.
"""

PROMPT_V2 = """
**Role:** Expert Film Editor specializing in content pacing and viewer retention.

**Task:** Generate a tightly-paced breakdown that prioritizes **viewer engagement and retention** by assigning precise word counts and time blocks.

**Context:**
The content is intended for **{target_platform}**. The length and pacing constraints of this platform must heavily influence the breakdown.
1. IDEA NAME: {idea_name}
2. GLOBAL MOOD: {global_mood}
3. RAW CONTENT: 
---
{raw_content}
---

**Reasoning:** Pacing is critical for the `{target_platform}`. Word counts must reflect desired on-screen time for optimal rhythm. Each scene's suggested **word_count** must be carefully calculated to reflect the desired on-screen time.

**Output Format:** Strict **JSON object** adhering to the required `ScriptBreakdown` schema, with emphasis on the `word_count` field for each scene.

**Stop Conditions:** Provide *only* the JSON object. No preamble, commentary, or explanation is permitted before or after the JSON block.
"""

PROMPT_V3 = """
**Role:** Creative Director and Narrative Architect.

**Task:** Craft a **high-impact narrative breakdown** focusing on a strong hook and clear conclusion based on the content.

**Context:**
Utilize the raw content to build a compelling story for **{target_platform}**. The narrative must align with the requested **{global_mood}**.
1. IDEA NAME: {idea_name}
2. GLOBAL MOOD: {global_mood}
3. RAW CONTENT: 
---
{raw_content}
---

**Reasoning:** Every successful video requires a compelling narrative arc: Hook, Body, and strong Conclusion/CTA. The breakdown must align with the `{global_mood}` and deliver maximum value in each segment.

**Output Format:** Strict **JSON object** adhering to the required `ScriptBreakdown` schema. The JSON must explicitly outline the content for the opening hook and final call-to-action.

**Stop Conditions:** Halt generation immediately after the complete JSON structure is outputted.
"""

def get_llama_prompt(version, idea_name, global_mood, raw_content, target_platform):
    """Selects and formats the appropriate Llama prompt."""
    
    if version == 'V1_Analytical':
        base_template = PROMPT_V1
    elif version == 'V2_Pacing':
        base_template = PROMPT_V2
    elif version == 'V3_Narrative':
        base_template = PROMPT_V3
    else:
        base_template = PROMPT_V1 

    system_prompt = (
        "You are an expert script structure analyst. Your task is to analyze the user's raw idea "
        "and output a structured script breakdown in **JSON format only**. "
        "Adhere to the JSON schema strictly and do not include any text outside of the JSON block."
    )
    
    # 3. Apply the context variables to the selected prompt template
    user_prompt = base_template.format(
        idea_name=idea_name,
        global_mood=global_mood,
        raw_content=raw_content,
        target_platform=target_platform
    )

    # 4. Combine into the Ollama / Llama messages format
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


# =========================================================================
# --- Helper Functions for File Parsing ---
# =========================================================================
def extract_text_from_file(uploaded_file):
    """Parses text from various file types."""
    name, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()
    
    if uploaded_file.size == 0:
        return "ERROR: Empty file uploaded."
        
    uploaded_file.seek(0) 

    if ext == '.txt':
        return uploaded_file.read().decode('utf-8')
    
    elif ext in ['.doc', '.docx']:
        if Document:
            try:
                document = Document(uploaded_file)
                return '\n'.join([paragraph.text for paragraph in document.paragraphs])
            except Exception as e:
                return f"ERROR: Could not parse Word document. {e}"
        else:
            return "ERROR: python-docx not installed."

    elif ext == '.pdf':
        if PdfReader:
            try:
                reader = PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e:
                return f"ERROR: Could not parse PDF document. {e}"
        else:
            return "ERROR: PyPDF not installed."

    return "ERROR: Unsupported file type or no file uploaded."


# =========================================================================
# --- Django Views ---
# =========================================================================

class ContentListView(ListView):
    """Displays the list of all content ideas (excluding soft deleted)."""
    model = ContentIdea
    template_name = 'content_recorder/content_list.html'
    context_object_name = 'ideas'
    ordering = ['-created_at'] 

class ContentDetailView(DetailView):
    """
    Displays a single content idea detail page and fetches the related 
    ScriptBreakdown object for display.
    """
    model = ContentIdea
    template_name = 'content_recorder/content_detail.html'
    context_object_name = 'idea'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        idea = self.get_object() 
        
        try:
            # Attempts to get the related ScriptBreakdown object.
            context['breakdown'] = idea.breakdown
        except ScriptBreakdown.DoesNotExist:
            context['breakdown'] = None
            
        return context


class ContentRecordView(View):
    """Handles both GET (show form) and POST (save new idea) for recording content."""
    def get(self, request):
        form = ContentIdeaForm()
        return render(request, 'content_recorder/record_content.html', {'form': form})

    def post(self, request):
        idea_name = request.POST.get('idea_name', '').strip()
        pasted_content = request.POST.get('raw_content', '').strip()
        uploaded_file = request.FILES.get('uploaded_file')
        
        raw_content = ""
        source_type = None
        source_data = None

        if uploaded_file:
            raw_content = extract_text_from_file(uploaded_file)
            source_type = ContentSource.SourceType.FILE
            source_data = uploaded_file.name
        
        elif pasted_content:
            raw_content = pasted_content
            source_type = ContentSource.SourceType.TEXT
            source_data = "Pasted Content"
        
        if not raw_content or raw_content.startswith("ERROR:"):
            messages.error(request, f"Submission failed: {raw_content or 'Please paste content or upload a valid file.'}")
            return redirect('content_recorder:record')

        try:
            with transaction.atomic():
                new_idea = ContentIdea.objects.create(
                    idea_name=idea_name,
                    raw_content=raw_content,
                    status=ContentIdea.StatusChoices.DRAFT
                )
                
                if source_data:
                    ContentSource.objects.create(
                        idea=new_idea,
                        source_type=source_type,
                        source_data=source_data,
                        description=f"Initial content captured from {source_data}"
                    )
                
                IdeaLog.objects.create(
                    idea=new_idea,
                    user=request.user if request.user.is_authenticated else None,
                    action="Idea Recorded"
                )
            
            messages.success(request, f"Content Idea '{new_idea.idea_name}' saved successfully!")
            return redirect('content_recorder:detail', pk=new_idea.pk)
        
        except Exception as e:
            messages.error(request, f"A database error occurred: {e}")
            return redirect('content_recorder:record')


class ContentUpdateView(UpdateView):
    """Handles editing an existing idea."""
    model = ContentIdea
    form_class = ContentIdeaForm 
    template_name = 'content_recorder/record_content.html' 
    context_object_name = 'idea' 
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        messages.success(self.request, f"Idea '{self.object.idea_name}' updated successfully.")
        return reverse_lazy('content_recorder:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        old_idea = ContentIdea.objects.get(pk=self.object.pk)
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            change_desc = ", ".join(form.changed_data)
            
            if 'status' in form.changed_data:
                old_status = old_idea.get_status_display()
                new_status = self.object.get_status_display()
                log_action = f"Status changed from '{old_status}' to '{new_status}'"
                change_desc = log_action if not change_desc else log_action + " and " + change_desc.replace('status', '').strip(', ')
            
            if change_desc:
                IdeaLog.objects.create(
                    idea=self.object,
                    user=self.request.user if self.request.user.is_authenticated else None,
                    action=f"Updated: {change_desc}"
                )
            
            return response

# --- Content Trash View (Soft Delete) ---
class ContentTrashView(View):
    """Handles soft deleting (moving to trash) an idea."""
    def post(self, request, pk):
        idea = get_object_or_404(ContentIdea.all_objects, pk=pk)
        
        idea.is_deleted = True
        idea.save()

        IdeaLog.objects.create(
            idea=idea,
            user=request.user if request.user.is_authenticated else None,
            action=f"Idea moved to Trash (Soft Delete)"
        )
        
        messages.warning(request, f"Idea '{idea.idea_name}' moved to trash.")
        return redirect('content_recorder:list') 
    
    def get(self, request, pk):
        idea = get_object_or_404(ContentIdea.all_objects, pk=pk)
        return render(request, 'content_recorder/idea_confirm_trash.html', {'idea': idea})
    

# --- LLM Control Views ---

class ScriptControlsView(View):
    """Renders the form to collect LLM parameters."""
    template_name = 'script_writer/script_generation_controls.html' 
    
    def get(self, request, pk):
        idea = get_object_or_404(ContentIdea, pk=pk)
        return render(request, self.template_name, {'idea': idea})

class ScriptGenerationActionView(View):
    """Handles the form submission, calls Ollama (Llama 3), and saves results."""
    
    def post(self, request, pk):
        idea = get_object_or_404(ContentIdea, pk=pk)
        
        # 1. Capture ALL parameters from the form
        target_platform = request.POST.get('target_platform')
        global_mood = request.POST.get('global_mood')
        llm_prompt_version = request.POST.get('llm_prompt_version')
        target_audience = request.POST.get('target_audience') or 'N/A'
        max_word_count = request.POST.get('max_word_count') or 'N/A'
        
        # 2. Prepare the prompt for Llama 3
        llama_messages = get_llama_prompt(
            version=llm_prompt_version,
            idea_name=idea.idea_name,
            global_mood=global_mood,
            raw_content=idea.raw_content,
            target_platform=target_platform
        )

        # 3. Construct the Ollama API request payload
        payload = {
            "model": settings.OLLAMA_MODEL_NAME, 
            "messages": llama_messages,
            "response_format": {"type": "json"},
            "stream": False
        }

        # 4. Make the API Call
        try:
            ollama_url = f"{settings.OLLAMA_HOST}/api/chat"
            # Setting a generous timeout since LLM calls can be slow
            response = requests.post(ollama_url, json=payload, timeout=120) 
            response.raise_for_status() 
            
            ollama_data = response.json()
            raw_json_string = ollama_data['message']['content']
            
            # CRITICAL: Parse the JSON string into a Python dictionary
            llm_output_data = json.loads(raw_json_string) 

        except requests.exceptions.RequestException as e:
            messages.error(request, f"Ollama Connection Error: Could not reach Llama 3. Ensure Ollama is running. Error: {e}")
            return redirect('content_recorder:detail', pk=pk)
        except json.JSONDecodeError:
            messages.error(request, "LLM returned invalid JSON. Try adjusting the prompt constraints or running the LLM locally to debug the output.")
            return redirect('content_recorder:detail', pk=pk)
            
        # 🚨 TEMPORARY DEBUG PRINT: Check LLM data structure before save 🚨
        print("\n--- LLM OUTPUT DATA RECEIVED AND PARSED SUCCESSFULLY ---")
        print(f"Data Type: {type(llm_output_data)}")
        # Print a sample of the scene data to ensure structure is correct
        try:
            # Added more defensive key access for the print statement
            print(f"Scene Sample: {llm_output_data.get('script_breakdown', {}).get('scenes', [{}])[0]}")
        except:
             print("Scene Sample: Could not access scene data.")
        print("----------------------------------------------------------\n")

        # 5. Save the Breakdown to the Database (COMPREHENSIVE TRY BLOCK)
        try:
            with transaction.atomic():
                # Get or create the Breakdown object
                try:
                    # Update existing breakdown if it exists
                    breakdown_obj = idea.breakdown
                except ScriptBreakdown.DoesNotExist:
                    # Create a new breakdown if it doesn't exist
                    breakdown_obj = ScriptBreakdown(idea=idea)
                
                # Assign all fields
                breakdown_obj.breakdown_data = llm_output_data 
                breakdown_obj.prompt_used = llm_prompt_version
                breakdown_obj.target_platform = target_platform
                breakdown_obj.global_mood = global_mood
                breakdown_obj.target_audience = target_audience
                breakdown_obj.save() # Save the breakdown object

                # Update Idea Status and Log
                idea.status = 'Script'
                idea.save() # Save the idea status
            
                log_action = f"Successfully generated and saved Script Breakdown from Ollama using {llm_prompt_version}."
                IdeaLog.objects.create(idea=idea, user=request.user if request.user.is_authenticated else None, action=log_action)
                
                messages.success(request, f"Script breakdown for '{idea.idea_name}' created successfully!")
                return redirect('content_recorder:detail', pk=pk)

        except Exception as e:
            # Catches IntegrityError, DataError (e.g., data too long), and all other exceptions during save
            messages.error(request, f"Database SAVE FAILED for breakdown: {type(e).__name__}: {e}. Check model field sizes vs LLM output.")
            return redirect('content_recorder:detail', pk=pk)