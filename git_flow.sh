#!/bin/bash

# --- Automated Git Flow Script ---

# 1. Check for staged changes
if git diff --cached --exit-code; then
    echo "❌ No changes detected. Did you forget to 'git add' files?"
    exit 1
fi

# 2. Get the commit message from the user
read -p "Enter your commit message: " COMMIT_MESSAGE

if [ -z "$COMMIT_MESSAGE" ]; then
    echo "❌ Commit message cannot be empty. Aborting."
    exit 1
fi

echo -e "\n--- Running Git Workflow ---\n"

# 3. Add all tracked and modified files (use git add . carefully or use git add -A)
echo "Staging all changes..."
git add -A
if [ $? -ne 0 ]; then
    echo "❌ Git add failed. Aborting."
    exit 1
fi

# 4. Commit changes
echo "Committing changes with message: \"$COMMIT_MESSAGE\""
git commit -m "$COMMIT_MESSAGE"
if [ $? -ne 0 ]; then
    echo "❌ Git commit failed. Aborting."
    exit 1
fi

# 5. Push to the main branch
echo "Pushing committed changes to remote 'origin/main'..."
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Git push failed. Please resolve merge conflicts or check connection."
    exit 1
fi

echo -e "\n✅ Git Workflow Complete! Changes are live on GitHub."