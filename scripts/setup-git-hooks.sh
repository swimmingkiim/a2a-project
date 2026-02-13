#!/bin/bash

# Ensure .git exists
if [ ! -d ".git" ]; then
    echo "❌ Error: .git directory not found. Run 'git init' first."
    exit 1
fi

HOOK_FILE=".git/hooks/pre-commit"

echo "#!/bin/bash" > $HOOK_FILE
echo "echo '🔒 Running Pre-Commit Security Scan...'" >> $HOOK_FILE
echo "python3 scripts/detect-secrets.py" >> $HOOK_FILE
echo "RESULT=\$?" >> $HOOK_FILE
echo "if [ \$RESULT -ne 0 ]; then" >> $HOOK_FILE
echo "    echo '❌ Security Check Failed. Commit blocked.'" >> $HOOK_FILE
echo "    exit 1" >> $HOOK_FILE
echo "fi" >> $HOOK_FILE
echo "exit 0" >> $HOOK_FILE

chmod +x $HOOK_FILE

echo "✅ Git Pre-commit Hook Installed!"
echo "   Now every commit will be scanned for secrets automatically."
