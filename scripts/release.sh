#!/bin/bash
set -e

# Packages list
PACKAGES=("trust-sdk" "api-sdk" "pay-sdk")

echo "🚀 Starting Release Process..."

# 1. Determine Root Version
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "Current Root Version: $CURRENT_VERSION"
echo "Select release type:"
echo "1) patch (default)"
echo "2) minor"
echo "3) major"
echo "4) manual input"
read -p "Enter choice [1-4]: " CHOICE

NEW_VERSION=""

if [ "$CHOICE" == "2" ]; then
    npm version minor --no-git-tag-version
elif [ "$CHOICE" == "3" ]; then
    npm version major --no-git-tag-version
elif [ "$CHOICE" == "4" ]; then
    read -p "Enter version (e.g. 1.0.0): " MANUAL_VERSION
    npm version $MANUAL_VERSION --no-git-tag-version
else
    npm version patch --no-git-tag-version
fi

NEW_ROOT_VERSION=$(node -p "require('./package.json').version")
echo "📌 Target Root Version: $NEW_ROOT_VERSION"

# 2. Bump Sub-packages and Collect Versions
PACKAGE_VERSIONS_MD="| Package | Version |\n|---------|---------|\n"

echo "📦 Bumping sub-packages..."
for pkg in "${PACKAGES[@]}"; do
    cd "packages/$pkg"
    # Always patch bump sub-packages for now as per requirement
    pnpm version patch --no-git-tag-version
    PKG_VERSION=$(node -p "require('./package.json').version")
    PACKAGE_VERSIONS_MD+="| \`$pkg\` | \`$PKG_VERSION\` |\n"
    cd ../..
    echo "  - $pkg -> $PKG_VERSION"
done

# 3. Commit and Push
echo "💾 Committing changes..."
git add package.json pnpm-lock.yaml packages/*/package.json
git commit -m "chore: release v$NEW_ROOT_VERSION"
git push

# 4. GitHub Release
echo "octocat: Creating GitHub Release..."
gh release create "v$NEW_ROOT_VERSION" --title "v$NEW_ROOT_VERSION" --generate-notes --notes "
## Included Packages

$PACKAGE_VERSIONS_MD
"

# 5. NPM Login
echo "🔑 Logging into NPM..."
npm login

# 6. Publish
echo "🚀 Publishing Packages..."
export SKIP_BUMP=true
./scripts/publish-packages.sh

echo "✅ Release v$NEW_ROOT_VERSION Complete!"
