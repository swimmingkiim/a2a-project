# @swimmingkiim/trust-sdk

A2A Trust SDK for Identity (DID), Verifiable Credentials (VC), and Reputation Management.

## Features

- **Identity Management**: Create and manage DIDs (did:key, did:ethr).
- **Verifiable Credentials**: Issue and verify W3C-compliant VCs.
- **Reputation**: Interact with the A2A reputation system.

## Installation

```bash
npm install @swimmingkiim/trust-sdk @veramo/core
```

## Usage

### Identity Management

```typescript
import { IdentityManager } from '@swimmingkiim/trust-sdk';

const idManager = new IdentityManager();
const did = await idManager.createEphemeralDID();
console.log('Created DID:', did);
```

### Verifiable Credentials

```typescript
// Assuming an initialized agent context
const credential = await agent.createVerifiableCredential({
  credential: {
    issuer: { id: myDID },
    credentialSubject: {
      id: targetDID,
      trustScore: 42
    }
  },
  proofFormat: 'jwt'
});
```
