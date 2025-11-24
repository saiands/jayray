#!/bin/bash

# --- Automated Git Flow Script ---

# 1. Add all changes
git add -A

# 2. Check for staged changes
if git diff --cached --exit-code; then
    echo "❌ No changes detected. Nothing to commit."
    exit 1
fi

# 3. Get the commit message from the user
read -p "Enter your commit message: " COMMIT_MESSAGE

if [ -z "$COMMIT_MESSAGE" ]; then
    echo "❌ Commit message cannot be empty. Aborting."
    exit 1
fi

echo -e "\n--- Running Git Workflow ---\n"

# 4. Commit changes
echo "Committing changes with message: \"$COMMIT_MESSAGE\""
git commit -m "$COMMIT_MESSAGE"

# 5. Push to the main branch
echo "Pushing committed changes to remote 'origin/main'..."
git push origin main

if [ $? -eq 0 ]; then
    echo -e "\n✅ Git Workflow Complete! Changes are live on GitHub."
else
    echo -e "\n❌ Git push failed. Please resolve merge conflicts or check your connection."
fi