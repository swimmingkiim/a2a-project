import os
import re

PATTERNS = {
    "ETH_PRIVATE_KEY": r"(?i)(private_?key|privatekey)[\s:=]+([\'\"]?)0x[a-fA-F0-9]{64}\2",
    "POSSIBLE_ETH_KEY": r"\b0x[a-fA-F0-9]{64}\b",
    "GENERIC_API_KEY": r"(?i)(api_?key|apikey|secret)[\s:=]+([\'\"]?)[a-zA-Z0-9_\-]{20,}\2",
    "GOOGLE_API_KEY": r"AIza[0-9A-Za-z\\-_]{35}",
}

# Standard ignores
IGNORE_DIRS = {".git", "node_modules", "dist", "build", "coverage", ".turbo"}
IGNORE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".ico", ".lock", ".json", ".lock.yaml"}

def scan_file(filepath):
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for name, pattern in PATTERNS.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    snippet = match.group(0)
                    # Filter out common false positives (like example/placeholder keys)
                    if "YOUR_" in snippet or "0x00000000" in snippet or "0x12345678" in snippet:
                        continue
                        
                    issues.append((name, snippet[:50]))
    except Exception:
        pass
    return issues

import sys

def main():
    print("--- Final Codebase Scan ---")
    current_issues = []
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in IGNORE_EXTENSIONS):
                continue
            if file == "detect-secrets.py" or file.startswith(".env"):
                continue
            
            filepath = os.path.join(root, file)
            # Scan file content
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    found_in_file = []
                    for name, pattern in PATTERNS.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            snippet = match.group(0)
                            # Filter out common false positives
                            if "YOUR_" in snippet or "0x00000000" in snippet or "0x12345678" in snippet:
                                continue
                            if "process.env" in snippet:
                                continue
                            # Whitelist known test keys
                            if "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" in snippet: # Hardhat Account 0
                                continue
                            if "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d" in snippet: # Test Logic Key
                                continue
                            if "0x0123456789012345678901234567890123" in snippet: # Obvious Dummy
                                continue
                            
                            # Whitelist Variable Names & References (False Positives)
                            if "A2A_PAYMASTER_API_KEY" in snippet:
                                continue
                            if "UPSTREAM_PAYMASTER_URL" in snippet:
                                continue
                            if "TREASURY_ADDRESS" in snippet:
                                continue
                            
                            # Whitelist Documentation Examples
                            if "a2a_sk_live_abc123" in snippet:
                                continue
                            
                            # Whitelist Transaction Hashes (often mistaken for keys)
                            if "0xfbb560ca2441fc18b70220d90cc509832ebbfac09e1588a592a198deb73e4f73" in snippet:
                                continue

                            found_in_file.append((name, snippet[:50]))
                    
                    if found_in_file:
                        print(f"\n[FLAG] {filepath}")
                        for name, snippet in found_in_file:
                            print(f"      - {name}: {snippet}...")
                        current_issues.append(filepath)

            except Exception:
                pass


    print("\n--- Summary ---")
    if current_issues:
        print(f"❌ FOUND POTENTIAL SECRETS IN {len(current_issues)} FILES.")
        print("Commit blocked! Please remove secrets or add to .gitignore.")
        sys.exit(1)
    else:
        print("✅ No secrets found. Proceeding...")
        sys.exit(0)

if __name__ == "__main__":
    main()
