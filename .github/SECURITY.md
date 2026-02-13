# Security Policy

## 🔒 Overview

This document outlines security guidelines for both **Service Providers** and **Service Users** in the A2A ecosystem.

---

## 🏗️ For Service Providers

### Never Commit to Repository

Your repository is public. **Never** include:

| ❌ Sensitive Data | Example |
|------------------|---------|
| Private Keys | DID private keys, wallet keys |
| API Keys | External service API keys |
| Database Credentials | DB connection strings |
| Treasury Addresses | Actual revenue wallet addresses |
| Secret Manager Keys | GCP/AWS secret keys |
| Environment Files | `.env`, `.env.local` |

### Use Environment Variables

**✅ Correct:**
```typescript
const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
```

**❌ Wrong:**
```typescript
// NEVER do this!
const TREASURY_ADDRESS = "0x1234567890abcdef...";
```

### Secure Deployment

Use **Google Cloud Secret Manager** for production:

```bash
# Create secret
gcloud secrets create treasury-address \
    --data-file=- <<< "0xYourActualAddress"

# Use in Cloud Run
gcloud run deploy ... \
    --set-secrets=TREASURY_ADDRESS=treasury-address:latest
```

### Verify .gitignore

Ensure these are in your `.gitignore`:

```
.env
.env.local
.env.*.local
*.key
*.pem
secrets/
```

### MCP Endpoint Security

- Use HTTPS in production
- Implement rate limiting
- Validate all input parameters with Zod schemas
- Log suspicious activities

---

## 🔍 For Service Users

### Verify Service Providers

Before connecting to any agent:

1. **Check Reputation Score**: Use OpenRank to verify trust
2. **Verify DID**: Ensure the DID is consistent across interactions
3. **Review Pricing**: Understand fee structures before transactions

### Session Key Best Practices

| Setting | Recommendation |
|---------|---------------|
| `maxAmount` | Set minimum needed for task |
| `validUntil` | Short duration (< 1 hour) |
| `targetService` | Specify exact DID |

**Example:**
```typescript
const sessionKey = await sessionKeyManager.createSession({
    maxAmount: "5 USDC",        // Only what you need
    validUntil: Date.now() + 900000, // 15 minutes
    targetService: "did:web:verified-agent.com"
});
```

### Protect Your Wallet

- Use separate wallets for different purposes
- Never share master private keys
- Monitor transaction history regularly
- Set up alerts for unusual activity

### Verify Tool Responses

- Validate response data formats
- Check for unexpected data patterns
- Implement error handling for failed calls

---

## 🐛 Vulnerability Reporting

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub Issue
2. Email security concerns directly to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
4. Expect response within 24-48 hours

---

## 🔐 Smart Contract Security

### For Providers Using Custom Contracts

- Get professional security audits
- Use established patterns (OpenZeppelin)
- Test extensively on testnet first
- Implement emergency pause mechanisms

### For Users Interacting with Contracts

- Verify contract addresses on block explorers
- Check if contracts are audited
- Start with small test transactions
- Understand gas implications

---

## 📜 Protocol Fee Integrity

The protocol fee mechanism is:
- **Protected by License**: Modification is prohibited
- **Transparent**: Fee rate (0.05%) is documented
- **Auditable**: On-chain transactions are verifiable

Attempting to bypass or modify fee collection code:
- Violates the A2A License
- May result in legal action
- Excludes you from ecosystem benefits

---

## ✅ Security Checklist

### Before Deploying (Providers)
- [ ] All secrets in Secret Manager
- [ ] No hardcoded credentials
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Input validation with Zod
- [ ] Logging enabled

### Before Transacting (Users)
- [ ] Agent reputation verified
- [ ] Session key properly scoped
- [ ] Maximum amount is limited
- [ ] Short validity period set
- [ ] Wallet has appropriate funds

---

**Remember: Code is open, secrets are not!**
