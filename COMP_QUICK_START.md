# $COMP System# Compute Token Quick Start
This guide helps you interact with the Compute Token (default symbol: $COMP) ecosystem.rs

## For Developers

### 1. Using USDC Fees (Existing)

```typescript
import { PaymasterManager } from '@swimmingkiim/pay-sdk';

const calls = [/* your transactions */];

const callsWithFee = PaymasterManager.appendFeeToCalls(calls, {
  treasury: process.env.TREASURY_ADDRESS,
  amount: 100000n,  // 0.1 USDC
  tokenType: 'USDC'
});
```

### 2. Using COMP Fees (New)

```typescript
const callsWithFee = PaymasterManager.appendFeeToCalls(calls, {
  treasury: process.env.TREASURY_ADDRESS,
  amount: 25n * 10n**18n,  // 25 COMP
  tokenType: 'COMP'
});
```

## For Operators

### Enable COMP Fees

1. **Update `.env`:**
   ```bash
   COMP_TOKEN_ADDRESS=0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3
   COMP_PRICE_USD=0.10
   ENABLE_COMP_FEES=true
   ```

2. **Restart Paymaster:**
   ```bash
   cd apps/paymaster
   pnpm build
   pnpm start
   ```

3. **Verify Logs:**
   ```
   ✅ COMP fee validation enabled (Token: 0xED17..., Price: $0.10)
   ```

## Test Results

- ✅ Smart Contract: 17/17 passing
- ✅ Oracle Layer: 15/15 passing
- ✅ Fee Validators: 7/7 passing
- ✅ SDK Integration: 4/4 passing
- **Total: 43/43 tests passing**

## Deployed Contracts

**ComputeToken (Base Sepolia):**  
`0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3`

## Documentation

- [Full Walkthrough](file:///Users/kimsooyoung/.gemini/antigravity/brain/63025d8d-84f6-409a-90bf-51fb9181ffea/walkthrough.md)
- [Phase 4 Implementation Plan](file:///Users/kimsooyoung/.gemini/antigravity/brain/63025d8d-84f6-409a-90bf-51fb9181ffea/phase4_integration_plan.md)
- [COMP Roadmap](file:///Users/kimsooyoung/Developments/projects/a2a-projects/plan/COMP_ROADMAP.md)
