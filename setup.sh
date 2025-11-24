#!/bin/bash
# Automation Script by Agent Nexus: Jayray Project Setup & Run

echo "Starting Jayray Project Setup..."

# 1. Check for Python Environment
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is required but not found. Please install it."
    exit 1
fi

# 2. Check for required libraries (DRF, file parsers conceptual)
echo "NOTE: Ensure required libraries (djangorestframework, python-docx, pypdf) are installed."
# pip install -r requirements.txt (Assuming requirements file exists)

# 3. Make Migrations for Content Recorder
echo "Making migrations for 'content_recorder'..."
python3 manage.py makemigrations content_recorder

# 4. Apply Database Migrations (creates the ContentIdea table)
echo "Applying database migrations..."
python3 manage.py migrate

# 5. Start the Django Development Server
echo "Starting Django Server at http://127.0.0.1:8000/content/"
python3 manage.py runserver 0.0.0.0:8000 # Use python3 explicitly for safety

echo "Setup script finished."