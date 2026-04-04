#!/bin/bash
# Deploy Perimeter Scout to Hugging Face Spaces
# Usage: ./deploy-to-huggingface.sh YOUR_USERNAME SPACE_NAME

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 YOUR_USERNAME SPACE_NAME"
    echo "Example: $0 myusername perimeter-scout"
    exit 1
fi

USERNAME=$1
SPACE_NAME=$2
HF_REMOTE="https://huggingface.co/spaces/${USERNAME}/${SPACE_NAME}"

echo "🚀 Deploying Perimeter Scout to Hugging Face Spaces"
echo "Target: ${HF_REMOTE}"
echo ""

# Check if huggingface remote already exists
if git remote | grep -q "^huggingface$"; then
    echo "✓ Hugging Face remote already configured"
    CURRENT_URL=$(git remote get-url huggingface)
    if [ "$CURRENT_URL" != "$HF_REMOTE" ]; then
        echo "⚠️  Current remote URL: $CURRENT_URL"
        echo "⚠️  New remote URL: $HF_REMOTE"
        read -p "Update remote URL? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git remote set-url huggingface "$HF_REMOTE"
            echo "✓ Remote URL updated"
        fi
    fi
else
    echo "→ Adding Hugging Face remote..."
    git remote add huggingface "$HF_REMOTE"
    echo "✓ Hugging Face remote added"
fi

echo ""
echo "→ Pushing to Hugging Face Spaces..."
git push huggingface HEAD:main

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Visit https://huggingface.co/spaces/${USERNAME}/${SPACE_NAME}/settings"
echo "2. Add the following secrets:"
echo "   - PIONEER_TRADER_URL: URL of your Pioneer Trader backend"
echo "   - AEGIS_COMMANDER_TOKEN: (Optional) Admin authentication token"
echo ""
echo "3. Test your deployment:"
echo "   curl https://${USERNAME}-${SPACE_NAME}.hf.space/api/v1/inventory/health"
echo ""
