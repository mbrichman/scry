#!/bin/bash
set -e

# Build script for deploying Dovos from private GitHub repository
# This handles SSH authentication for private repo access

echo "==== Dovos Build from GitHub ===="

# Configuration
GITHUB_REPO="${GITHUB_REPO:-git@github.com:mbrichman/dovos.git}"
BRANCH="${BRANCH:-main}"
IMAGE_NAME="${IMAGE_NAME:-dovos-rag}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Detect SSH agent socket
if [ -n "$SSH_AUTH_SOCK" ]; then
    # Use existing SSH_AUTH_SOCK (standard ssh-agent)
    SSH_SOCKET="$SSH_AUTH_SOCK"
    echo "✓ Using SSH agent: $SSH_AUTH_SOCK"
elif [ -S "$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock" ]; then
    # Use 1Password SSH agent (macOS)
    SSH_SOCKET="$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
    echo "✓ Using 1Password SSH agent"
elif [ -S "$HOME/.1password/agent.sock" ]; then
    # Use 1Password SSH agent (alternative location)
    SSH_SOCKET="$HOME/.1password/agent.sock"
    echo "✓ Using 1Password SSH agent"
else
    echo "❌ ERROR: No SSH agent found!"
    echo ""
    echo "Please start ssh-agent or 1Password SSH agent:"
    echo "  eval \$(ssh-agent -s)"
    echo "  ssh-add ~/.ssh/id_ed25519"
    echo ""
    echo "Or configure 1Password SSH agent."
    exit 1
fi

# Test GitHub connection
echo ""
echo "Testing GitHub SSH connection..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✓ GitHub SSH authentication successful"
else
    echo "❌ ERROR: GitHub SSH authentication failed"
    echo ""
    echo "Make sure your SSH key is added to GitHub:"
    echo "  https://github.com/settings/keys"
    exit 1
fi

# Build the image
echo ""
echo "Building Docker image..."
echo "  Repository: $GITHUB_REPO"
echo "  Branch: $BRANCH"
echo "  Image: $IMAGE_NAME:$IMAGE_TAG"
echo ""

DOCKER_BUILDKIT=1 docker build -f Dockerfile.git.ssh \
  --ssh default="$SSH_SOCKET" \
  --build-arg GITHUB_REPO="$GITHUB_REPO" \
  --build-arg BRANCH="$BRANCH" \
  -t "$IMAGE_NAME:$IMAGE_TAG" \
  .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "Image: $IMAGE_NAME:$IMAGE_TAG"
    echo ""
    echo "To run the image:"
    echo "  docker compose up -d"
    echo ""
    echo "Or to run directly:"
    echo "  docker run -p 5001:5001 $IMAGE_NAME:$IMAGE_TAG"
else
    echo ""
    echo "❌ Build failed"
    exit 1
fi
