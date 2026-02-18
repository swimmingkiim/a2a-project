# DID Selection Guide

## What is a DID (Decentralized Identifier)?

A DID is a decentralized identifier that proves ownership of a project or individual. When registering a project on the A2A Agent Node, you must set an Owner DID.

## DID Format Comparison

### ✅ Recommended: `did:web` (Web-based DID)

**Format**: `did:web:yourdomain.com` or `did:web:api.yourdomain.com`

**Examples**:
- `did:web:api.swimmingkiim.com`
- `did:web:myproject.vercel.app`
- `did:web:example.com:api:v1`

**Advantages**:
- ✅ **No private key exposure risk**
- ✅ Prove identity through domain ownership
- ✅ Verifiable via DNS
- ✅ Most secure method

**Disadvantages**:
- Requires a domain
- DID becomes invalid if domain expires

**Verification Method**:
```
https://yourdomain.com/.well-known/did.json
```
Host a DID Document at this path to prove ownership

---

### ⚠️ Caution: `did:ethr` (Ethereum address-based)

**Format**: `did:ethr:0x<ethereum_address>`

**Examples**:
- `did:ethr:0x1b47594E05D3eC70E5466C8aC65F8832746Ac15B`

**Advantages**:
- ✅ Verifiable via blockchain address
- ✅ No additional infrastructure needed

**Warnings**:
- ⚠️ **Your actual Ethereum address becomes public**
- ⚠️ Risk of asset exposure if using main wallet address
- ⚠️ All on-chain activity is traceable

**Recommendations**:
- Create and use a dedicated address
- Never use your main wallet address
- Use an empty address with no assets

---

### ❌ Not Recommended: `did:pkh` (Public Key Hash-based)

**Format**: `did:pkh:eip155:<chain_id>:<address>`

**Examples**:
- `did:pkh:eip155:8453:0x1b47594E05D3eC70E5466C8aC65F8832746Ac15B`

**Issues**:
- ❌ Risk of private key information leakage
- ❌ Chain-specific address exposure
- ❌ Security vulnerabilities

**Not recommended for use**

---

## Security Recommendations

### 1. Use did:web (Highest Priority)

```
did:web:api.yourproject.com
```

**Setup Instructions**:
1. Prepare a domain (e.g., api.yourproject.com)
2. Create `/.well-known/did.json` file
3. Write DID Document:

```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:web:api.yourproject.com",
  "verificationMethod": [{
    "id": "did:web:api.yourproject.com#key-1",
    "type": "JsonWebKey2020",
    "controller": "did:web:api.yourproject.com",
    "publicKeyJwk": {
      "kty": "EC",
      "crv": "secp256k1",
      "x": "...",
      "y": "..."
    }
  }]
}
```

### 2. Precautions When Using did:ethr

If you must use did:ethr:

1. **Create a Dedicated Wallet Address**
   ```bash
   # Generate new wallet (never store assets)
   ```

2. **Separate from Main Wallet**
   - Main wallet: For asset storage
   - DID-only wallet: For identity verification only

3. **Regular Monitoring**
   - Check for suspicious transactions to that address

### 3. Absolute Prohibitions

❌ **Never provide private keys directly to bots**
- Bots may auto-register with did:ethr format, exposing your address
- Use did:web instead or register manually

❌ **Never expose DIDs of wallets in active use**
- Assets become traceable
- Privacy invasion

## Practical Examples

### Good Examples ✅

```javascript
// API deployed on Vercel/Netlify
const goodDID = "did:web:my-api.vercel.app";

// Custom domain
const alsoGoodDID = "did:web:api.myproject.com";
```

### Bad Examples ❌

```javascript
// Using main wallet address
const badDID = "did:ethr:0xMyMainWalletWith1000ETH";

// Bot auto-registered private key-based DID
const veryBadDID = "did:pkh:eip155:8453:0xExposedPrivateKey";
```

## Registration Requirements: `ownerWallet` and `DID`

When registering a project or applying for a Developer Grant, two identifiers are required:

### `ownerWallet` — Ethereum Wallet Address

**Must be an Ethereum address**, not a web URL.

```
✅ Correct: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0
❌ Wrong:   https://mybot.com
❌ Wrong:   did:web:mybot.com
```

### `DID` — Decentralized Identifier

The current Paymaster registration API (`/v1/register`) extracts an Ethereum address from the DID string. Therefore, **the DID must contain an `0x` address**:

```
✅ Supported: did:ethr:0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0
⚠️ Not yet supported by registration API: did:web:api.mybot.com
```

> [!IMPORTANT]
> **`ownerWallet` and DID must reference the same Ethereum address.**
> The Grant handler (`grant-handler.ts`) matches the `walletAddress` claim in your Verifiable Credential against registered `owner_wallet` in the database. If they differ, the Grant application will be rejected with _"Wallet address is not associated with a registered project"_.

### Quick Reference

| Field | Format | Example |
|-------|--------|---------|
| `ownerWallet` | Ethereum address (`0x...`) | `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0` |
| `DID` (registration) | `did:ethr:0x...` | `did:ethr:0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0` |
| `DID` (production, future) | `did:web:domain` | `did:web:api.mybot.com` |

---

## Summary

| DID Format | Security | Privacy | Convenience | Recommendation |
|-----------|----------|---------|-------------|----------------|
| `did:web` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Strongly Recommended |
| `did:ethr` (dedicated) | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⚠️ Use with Caution |
| `did:ethr` (main) | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ❌ Do Not Use |
| `did:pkh` | ⭐ | ⭐ | ⭐⭐⭐ | ❌ Do Not Use |

## Conclusion

**Safest Choice**: `did:web:yourdomain.com`

Prove ownership with just a domain, without worrying about private key exposure.
