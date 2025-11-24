# --- 1. Create Directories ---
mkdir -p content_recorder/templates/content_recorder
mkdir -p project

# --- 2. Create Python Files ---

# content_recorder/models.py (Agent Titan)
cat > content_recorder/models.py << EOL
from django.db import models

class ContentIdea(models.Model):
    content_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="Content ID"
    )
    idea_name = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="Idea Name/Title"
    )
    raw_content = models.TextField(
        verbose_name="Original Content"
    )
    source_file_name = models.CharField(
        max_length=255, 
        null=True, blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.idea_name:
            count = ContentIdea.objects.all().count() + 1
            self.idea_name = f"idea_{count}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.idea_name
EOL

# content_recorder/views.py (Backend Logic)
cat > content_recorder/views.py << EOL
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .models import ContentIdea
import os

# --- Dummy File Parsing Placeholder ---
# NOTE: Replace with actual libraries (python-docx, pypdf) installation later
def extract_text_from_file(uploaded_file):
    name, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()
    
    if ext == '.txt':
        return uploaded_file.read().decode('utf-8')
    elif ext in ['.doc', '.docx', '.pdf']:
        # This is a dummy for demonstration without external libs installed
        return f"Successfully detected file {uploaded_file.name}. Actual parsing logic needs external libraries."
    return "ERROR: Unsupported file type."

# --- Django Views ---

class ContentListView(View):
    def get(self, request):
        ideas = ContentIdea.objects.all()
        return render(request, 'content_recorder/content_list.html', {'ideas': ideas})

class ContentDetailView(View):
    def get(self, request, pk):
        idea = get_object_or_404(ContentIdea, pk=pk)
        return render(request, 'content_recorder/content_detail.html', {'idea': idea})

class ContentRecordView(View):
    def get(self, request):
        return render(request, 'content_recorder/record_content.html')

    def post(self, request):
        idea_name = request.POST.get('idea_name', '').strip()
        pasted_content = request.POST.get('pasted_content', '').strip()
        uploaded_file = request.FILES.get('uploaded_file')
        
        raw_content = ""
        source_file_name = None

        if uploaded_file:
            raw_content = extract_text_from_file(uploaded_file)
            source_file_name = uploaded_file.name
        
        if pasted_content:
            raw_content = pasted_content
        
        if not raw_content:
            messages.error(request, "Submission failed: Please paste content or upload a valid file.")
            return redirect('content_recorder:record')

        try:
            ContentIdea.objects.create(
                idea_name=idea_name,
                raw_content=raw_content,
                source_file_name=source_file_name
            )
            messages.success(request, f"Content Idea saved successfully!")
            return redirect('content_recorder:list')
        
        except Exception as e:
            messages.error(request, f"A database error occurred: {e}")
            return redirect('content_recorder:record')
EOL

# content_recorder/urls.py (Agent Nexus)
cat > content_recorder/urls.py << EOL
from django.urls import path
from .views import ContentRecordView, ContentListView, ContentDetailView

app_name = 'content_recorder' 

urlpatterns = [
    path('', ContentListView.as_view(), name='list'), 
    path('record/', ContentRecordView.as_view(), name='record'),
    path('detail/<int:pk>/', ContentDetailView.as_view(), name='detail'),
]
EOL

# project/urls.py (Agent Nexus)
cat > project/urls.py << EOL
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='content/', permanent=True)), 
    path('content/', include('content_recorder.urls', namespace='content_recorder')), 
]
EOL


# --- 3. Create HTML Template Files ---

# content_recorder/templates/content_recorder/base.html (Agent Aura Header)
cat > content_recorder/templates/content_recorder/base.html << EOL
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jayray | {% block title %}{% endblock %}</title>
    <style>
        :root { --primary-color: #007aff; --background-color: #f5f5f7; --header-bg: rgba(255, 255, 255, 0.95); --text-color: #1d1d1f; --border-color: #d2d2d7; --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { margin: 0; padding-top: 60px; font-family: var(--font-family); background-color: var(--background-color); color: var(--text-color); }
        #main-header { position: fixed; top: 0; left: 0; right: 0; height: 50px; background-color: var(--header-bg); backdrop-filter: saturate(180%) blur(5px); border-bottom: 1px solid var(--border-color); z-index: 1000; display: flex; align-items: center; justify-content: center; }
        .nav-menu { width: 100%; max-width: 1000px; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; }
        .brand-name { font-size: 1.2rem; font-weight: 600; color: var(--text-color); text-decoration: none; }
        .app-links a { margin-left: 20px; color: #515154; text-decoration: none; font-size: 0.85rem; transition: color 0.2s; }
        .app-links a:hover, .app-links a.active { color: var(--text-color); font-weight: 500; }
        .content { max-width: 900px; margin: 40px auto; padding: 0 20px; }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <header id="main-header">
        <nav class="nav-menu">
            <a href="{% url 'content_recorder:list' %}" class="brand-name">Jayray</a>
            <div class="app-links">
                <a href="{% url 'content_recorder:list' %}" class="active">Content Recorder</a>
                <a href="#">Script Writer</a>
                <a href="#">Storyboard</a>
                <a href="#">Image Generator</a>
                <a href="#">Video Creator</a>
            </div>
        </nav>
    </header>

    <div class="content">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
EOL

# content_recorder/templates/content_recorder/record_content.html (Agent Aura Form)
cat > content_recorder/templates/content_recorder/record_content.html << EOL
{% extends "content_recorder/base.html" %}

{% block title %}Record New Content{% endblock %}

{% block extra_css %}
<style>
    .content-submission-area h2 { font-size: 2rem; font-weight: 700; margin-bottom: 30px; text-align: center; }
    .upload-form { background: #fff; border-radius: 12px; padding: 40px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05); }
    .input-title, .expandable-textarea { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); border-radius: 8px; box-sizing: border-box; font-size: 1rem; transition: border-color 0.2s, box-shadow 0.2s; }
    .input-title:focus, .expandable-textarea:focus { border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2); outline: none; }
    .expandable-textarea { resize: vertical; min-height: 250px; font-family: var(--font-family); }
    .file-upload-section { margin-top: 10px; padding: 20px 0; border-top: 1px dashed var(--border-color); display: flex; align-items: center; justify-content: space-between; }
    .custom-file-upload { display: inline-block; background-color: #e5e5ea; color: var(--text-color); padding: 10px 15px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: background-color 0.2s; }
    .custom-file-upload:hover { background-color: #d1d1d6; }
    #file-upload { display: none; }
    #file-name-display { color: #515154; font-size: 0.9rem; }
    .cta-button { width: 100%; background-color: var(--primary-color); color: white; padding: 15px; border: none; border-radius: 8px; font-size: 1.1rem; font-weight: 600; cursor: pointer; margin-top: 30px; transition: background-color 0.2s; }
    .cta-button:hover { background-color: #005bb5; }
</style>
{% endblock %}

{% block content %}
<section class="content-submission-area">
    <h2>Capture Your Idea</h2>
    
    {% if messages %}
        {% for message in messages %}
            <div style="padding:10px; background-color:#f8d7da; color:#721c24; border-radius:5px; margin-bottom:15px;">{{ message }}</div>
        {% endfor %}
    {% endif %}

    <form method="POST" enctype="multipart/form-data" class="upload-form">
        {% csrf_token %}
        
        <input type="text" name="idea_name" placeholder="Idea Title (Optional, will auto-fill if blank)" class="input-title">

        <textarea name="pasted_content" id="pasted-content" 
                  placeholder="Paste your content here..."
                  rows="10" 
                  class="expandable-textarea"></textarea>

        <div class="file-upload-section">
            <div>
                <label for="file-upload" class="custom-file-upload">
                    Upload Text File (.txt, .doc, .pdf)
                </label>
                <input id="file-upload" type="file" name="uploaded_file" accept=".txt,.doc,.docx,.pdf">
            </div>
            <span id="file-name-display">No file selected.</span>
        </div>
        
        <button type="submit" class="cta-button">Process & Save Idea</button>
    </form>
</section>

<script>
    document.getElementById('file-upload').addEventListener('change', function() {
        const fileName = this.files.length > 0 ? this.files[0].name : 'No file selected.';
        document.getElementById('file-name-display').textContent = fileName;
    });
</script>
{% endblock %}
EOL

# content_recorder/templates/content_recorder/content_list.html (Agent Aura List)
cat > content_recorder/templates/content_recorder/content_list.html << EOL
{% extends "content_recorder/base.html" %}

{% block title %}Content Ideas List{% endblock %}

{% block extra_css %}
<style>
    .content-list-area h2 { font-size: 2rem; font-weight: 700; margin-bottom: 30px; }
    .content-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05); }
    .content-table th, .content-table td { padding: 15px 20px; text-align: left; border-bottom: 1px solid var(--border-color); }
    .content-table th { background-color: #fafafa; font-weight: 600; color: #515154; font-size: 0.9rem; }
    .content-table tr:last-child td { border-bottom: none; }
    .content-table tr:hover { background-color: #f0f0f5; cursor: pointer; }
    .idea-link { color: var(--primary-color); text-decoration: none; font-weight: 500; }
    .date-col { white-space: nowrap; }
    .new-idea-button { display: inline-block; background-color: var(--primary-color); color: white; padding: 10px 20px; border-radius: 8px; font-size: 1rem; font-weight: 600; text-decoration: none; margin-bottom: 20px; transition: background-color 0.2s; }
    .new-idea-button:hover { background-color: #005bb5; }
</style>
{% endblock %}

{% block content %}
<section class="content-list-area">
    <h2>All Content Ideas</h2>
    <a href="{% url 'content_recorder:record' %}" class="new-idea-button">➕ Record New Idea</a>

    {% if ideas %}
    <table class="content-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Idea Name</th>
                <th>Created Date</th>
                <th>Created Time</th>
            </tr>
        </thead>
        <tbody>
            {% for idea in ideas %}
            <tr onclick="window.location.href='{% url 'content_recorder:detail' pk=idea.content_id %}'">
                <td>{{ idea.content_id }}</td>
                <td><a href="{% url 'content_recorder:detail' pk=idea.content_id %}" class="idea-link">{{ idea.idea_name }}</a></td>
                <td class="date-col">{{ idea.created_at|date:"Y-m-d" }}</td>
                <td class="date-col">{{ idea.created_at|date:"h:i A" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="text-align: center; margin-top: 50px; color: #515154;">No content ideas recorded yet. Start by recording a new idea!</p>
    {% endif %}
</section>
{% endblock %}
EOL

# content_recorder/templates/content_recorder/content_detail.html (Basic Detail View)
cat > content_recorder/templates/content_recorder/content_detail.html << EOL
{% extends "content_recorder/base.html" %}

{% block title %}Idea Detail: {{ idea.idea_name }}{% endblock %}

{% block content %}
<section class="content-detail-area">
    <h2>Idea: {{ idea.idea_name }} (ID: {{ idea.content_id }})</h2>
    <p><strong>Created At:</strong> {{ idea.created_at }}</p>
    <p><strong>Source File:</strong> {{ idea.source_file_name|default:"Pasted Content" }}</p>
    
    <hr style="margin: 30px 0; border: 0; border-top: 1px solid #ccc;">

    <h3>Raw Content</h3>
    <pre style="white-space: pre-wrap; background: #fff; padding: 20px; border-radius: 8px; border: 1px solid var(--border-color);">{{ idea.raw_content }}</pre>

    <div style="margin-top: 30px;">
        <a href="{% url 'content_recorder:list' %}" style="color: var(--primary-color); text-decoration: none;">&larr; Back to List</a>
    </div>
    
    <a href="#" style="background-color: #28a745; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; margin-top: 20px; display: inline-block;">Start Script Writing Workflow &rarr;</a>

</section>
{% endblock %}
EOL

# --- 4. Automation Script (Agent Nexus) ---

# setup.sh
cat > setup.sh << EOL
#!/bin/bash
# Automation Script by Agent Nexus: Jayray Project Setup & Run

echo "Starting Jayray Project Setup..."

# 1. Create a minimal settings.py if it doesn't exist (assuming you've done the basic Django startproject)
if [ ! -f "project/settings.py" ]; then
    echo "WARNING: project/settings.py not found. Using dummy content. Please run 'django-admin startproject project .' first."
    echo "You must manually configure DATABASES and add 'content_recorder' to INSTALLED_APPS."
fi

# 2. Make Migrations for Content Recorder
echo "Making migrations for 'content_recorder'..."
python3 manage.py makemigrations content_recorder

# 3. Apply Database Migrations
echo "Applying database migrations..."
python3 manage.py migrate

# 4. Start the Django Development Server
echo "Starting Django Server at http://127.0.0.1:8000/content/"
python3 manage.py runserver 0.0.0.0:8000 

echo "Setup script finished."
EOL

# --- 5. Set Permissions and Run Instructions ---
chmod +x setup.sh

echo ""
echo "✅ **All files have been created/updated!**"
echo "You should now have the following directory structure in your current folder:"
echo "jayray_project/"
echo "├── project/ (containing settings.py and urls.py)"
echo "└── content_recorder/ (containing models.py, views.py, urls.py, and templates)"
echo "└── setup.sh"
echo ""
echo "### 🚀 Next Step: Execute the Project"
echo "1. **Ensure you have a basic Django project** (settings.py, manage.py) and necessary libraries installed (Django, etc.)."
echo "2. **Run the automation script** by executing the following command:"
echo ""
echo "    **./setup.sh**"
echo ""
echo "This will create the database tables and start the web server."