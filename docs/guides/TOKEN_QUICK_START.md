# $DAIM System — Utility Token Quick Start
This guide helps you interact with the $DAIM Token ecosystem.

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

### 2. Using DAIM Fees (New)

```typescript
const callsWithFee = PaymasterManager.appendFeeToCalls(calls, {
  treasury: process.env.TREASURY_ADDRESS,
  amount: 25n * 10n**18n,  // 25 DAIM
  tokenType: 'DAIM'
});
```

## For Operators

### Enable DAIM Fees

1. **Update `.env`:**
   ```bash
   DAIM_ADDRESS=0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2
   DAIM_PRICE_USD=0.10
   ENABLE_DAIM_FEES=true
   ```

2. **Restart Paymaster:**
   ```bash
   cd apps/paymaster
   pnpm build
   pnpm start
   ```

3. **Verify Logs:**
   ```
   ✅ DAIM fee validation enabled (Token: 0xE0Bf..., Price: $0.10)
   ```

## Test Results

- ✅ Smart Contract: 17/17 passing
- ✅ Oracle Layer: 15/15 passing
- ✅ Fee Validators: 7/7 passing
- ✅ SDK Integration: 4/4 passing
- **Total: 43/43 tests passing**

## Deployed Contracts

**DaimToken (Base Mainnet):**  
`0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2`

## Documentation

- [Paymaster Bot Guide](file:///Users/kimsooyoung/Developments/projects/a2a-projects/docs/guides/PAYMASTER_BOT_GUIDE.md)
- [AI Agent Token Guide](file:///Users/kimsooyoung/Developments/projects/a2a-projects/docs/guides/AI_AGENT_TOKEN_GUIDE.md)
