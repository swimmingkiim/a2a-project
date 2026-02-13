#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting A2A Packages Publishing Process..."

# Array of packages to publish
PACKAGES=("trust-sdk" "api-sdk" "pay-sdk")

# Function to publish a package
publish_package() {
    local pkg=$1
    echo "--------------------------------------------------"
    echo "📦 Processing package: $pkg"
    echo "--------------------------------------------------"
    
    cd "packages/$pkg"
    
    # Bump version automatically unless skipped
    if [ "$SKIP_BUMP" != "true" ]; then
        echo "Bumping patch version..."
        pnpm version patch --no-git-tag-version
    else
        echo "Skipping version bump (SKIP_BUMP=true)..."
    fi
    
    # Build
    echo "Building..."
    # Use pnpm to run the build script defined in package.json
    pnpm run build
    
    # Publish
    echo "Publishing to npm..."
    # --no-git-checks: Avoid failing if the repo is not clean (optional, but good for CI/hacking)
    pnpm publish --access public --no-git-checks
    
    echo "✅ Successfully published $pkg"
    
    # Go back to root
    cd ../..
}

# Main loop
# Ensure pnpm is available
if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm is not installed. Please install it first."
    exit 1
fi

echo "Installing workspace dependencies..."
pnpm install

for pkg in "${PACKAGES[@]}"; do
    publish_package "$pkg"
done

echo "--------------------------------------------------"
echo "🎉 All packages published successfully!"
echo "--------------------------------------------------"
