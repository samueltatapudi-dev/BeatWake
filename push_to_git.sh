#!/bin/bash

echo "🚀 Pushing BeatWake to GitHub..."
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Not a git repository. Initializing..."
    git init
    echo "✅ Git repository initialized"
fi

# Check git configuration
if [ -z "$(git config user.name)" ]; then
    echo "⚠️  Git user.name not set. Please run:"
    echo "   git config --global user.name 'Your Name'"
    exit 1
fi

if [ -z "$(git config user.email)" ]; then
    echo "⚠️  Git user.email not set. Please run:"
    echo "   git config --global user.email 'your.email@example.com'"
    exit 1
fi

# Stage all files
echo "📦 Staging files..."
git add .

# Show what will be committed
echo ""
echo "📝 Files to be committed:"
git status --short

# Commit changes
echo ""
read -p "Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Update BeatWake with new features and README"
fi

git commit -m "$commit_msg"
echo "✅ Changes committed"

# Check if remote exists
if ! git remote | grep -q "origin"; then
    echo ""
    echo "⚠️  No remote repository found."
    read -p "Enter your GitHub repository URL: " repo_url
    git remote add origin "$repo_url"
    echo "✅ Remote repository added"
fi

# Check current branch
current_branch=$(git branch --show-current)
if [ -z "$current_branch" ]; then
    current_branch="main"
    git branch -M main
    echo "✅ Branch renamed to main"
fi

# Push to remote
echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin "$current_branch"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "🎉 Your code is now on GitHub!"
else
    echo ""
    echo "❌ Push failed. You might need to authenticate or check your remote URL."
    echo "💡 Tips:"
    echo "   - Make sure you have access to the repository"
    echo "   - Check if you need to authenticate with: gh auth login"
    echo "   - Verify remote URL with: git remote -v"
fi
