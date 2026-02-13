# High Priority Tasks

## ✅ 1. Paymaster Code Cleanup

**Status:** Complete  
**Result:** 
- Build successful after adding `parseEther` import
- All 36 tests passing
- Code clean and production-ready

## ✅ 2. Base Mainnet Deployment Preparation

**Status:** Complete  
**Deliverable:** [MAINNET_DEPLOYMENT.md](file:///Users/kimsooyoung/Developments/projects/a2a-projects/MAINNET_DEPLOYMENT.md)

**Includes:**
- Pre-deployment checklist
- Step-by-step deployment guide
- Post-deployment validation
- Gradual rollout strategy (Days 1-7)
- Rollback plan
- Monitoring metrics
- Security checklist

---

# Medium Priority Tasks

## 1. Real Oracle Integration (Chainlink)

**Goal:** Replace MockTokenPriceOracle with Chainlink Price Feeds

**Implementation Plan:**

### A. Chainlink Price Feed Addresses (Base Mainnet)

```typescript
// COMP/USD - Will need custom oracle or use proxy method
// ETH/USD - 0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70

// For now: COMP/ETH via indirect calculation
// ETH/USD * COMP/ETH = COMP/USD
```

### B. Create ChainlinkOracle.ts

```typescript
import { createPublicClient, http } from 'viem';
import { ITokenPriceOracle } from './ITokenPriceOracle';

const CHAINLINK_ABI = [
  'function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)'
];

export class ChainlinkOracle implements ITokenPriceOracle {
  private client;
  private ethUsdFeed = '0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70';
  
  async getETHPriceUSD(): Promise<number> {
    const result = await this.client.readContract({
      address: this.ethUsdFeed,
      abi: CHAINLINK_ABI,
      functionName: 'latestRoundData'
    });
    
    // Chainlink returns 8 decimals for USD pairs
    return Number(result.answer) / 1e8;
  }
  
  // ... implement other methods
}
```

### C. Update Paymaster Integration

```typescript
// apps/paymaster/src/paymaster.ts

import { ChainlinkOracle } from './oracle/ChainlinkOracle';

const oracle = new ChainlinkOracle(config.RPC_URL);
compValidator = new COMPFeeValidator({
  treasuryAddress: config.TREASURY_ADDRESS,
  compTokenAddress: config.COMP_TOKEN_ADDRESS,
  markupRate: config.MARKUP_RATE
}, oracle);
```

### D. Fallback Strategy

```typescript
export class HybridOracle implements ITokenPriceOracle {
  constructor(
    private chainlinkOracle: ChainlinkOracle,
    private mockOracle: MockTokenPriceOracle
  ) {}
  
  async getETHPriceUSD(): Promise<number> {
    try {
      return await this.chainlinkOracle.getETHPriceUSD();
    } catch (error) {
      console.warn('Chainlink failed, using fallback');
      return await this.mockOracle.getETHPriceUSD();
    }
  }
}
```

**Estimated Time:** 2-3 hours  
**Dependencies:** None  
**Risk:** Low (fallback to Mock available)

---

## 2. Monitoring System

**Goal:** Real-time metrics and alerting

### A. Prometheus Metrics

```typescript
// apps/paymaster/src/metrics.ts

import { Counter, Histogram, Gauge } from 'prom-client';

export const feeValidationCounter = new Counter({
  name: 'fee_validation_total',
  help: 'Total fee validations',
  labelNames: ['tokenType', 'status']
});

export const feeValidationDuration = new Histogram({
  name: 'fee_validation_duration_seconds',
  help: 'Fee validation duration',
  labelNames: ['tokenType']
});

export const compPriceGauge = new Gauge({
  name: 'comp_price_usd',
  help: 'Current COMP price in USD'
});
```

### B. Usage in Validators

```typescript
// In USDCFeeValidator.validateFeeIncluded()
const timer = feeValidationDuration.startTimer({ tokenType: 'USDC' });

try {
  const result = await this.validate(userOp, client);
  feeValidationCounter.inc({ tokenType: 'USDC', status: result ? 'success' : 'failure' });
  return result;
} finally {
  timer();
}
```

### C. Grafana Dashboard

Create dashboard with:
- Fee validation rate (USDC vs COMP)
- Success/failure ratios
- Response times (p50, p95, p99)
- COMP price over time
- Error rates

**Estimated Time:** 4-6 hours  
**Dependencies:** Prometheus + Grafana setup  
**Risk:** Medium (requires infrastructure)

---

## 3. E2E Demo Script

**Goal:** Automated end-to-end test on Base Sepolia

### Implementation

```typescript
// scripts/e2e-demo.ts

import { privateKeyToAccount } from 'viem/accounts';
import { PaymasterManager } from '@swimmingkiim/pay-sdk';
import { createSmartAccountClient } from 'permissionless';

async function runE2EDemo() {
  console.log('🚀 Starting E2E Demo: COMP Fee Payment\n');
  
  // 1. Setup
  const owner = privateKeyToAccount(process.env.DEMO_PRIVATE_KEY);
  const smartAccount = await createSmartAccountClient({...});
  
  console.log('✅ Smart Account:', smartAccount.address);
  
  // 2. Check COMP balance
  const compBalance = await checkCOMPBalance(smartAccount.address);
  console.log(`💰 COMP Balance: ${compBalance} COMP`);
  
  if (compBalance < 25n) {
    console.log('⚠️  Insufficient COMP, minting...');
    await mintCOMP(smartAccount.address, 100n);
  }
  
  // 3. Create transaction with COMP fee
  const calls = [{
    to: '0x...',  // some target
    value: 0n,
    data: '0x'
  }];
  
  const callsWithFee = PaymasterManager.appendFeeToCalls(calls, {
    treasury: process.env.TREASURY_ADDRESS,
    amount: 25n * 10n**18n,  // 25 COMP
    tokenType: 'COMP'
  });
  
  console.log('📝 Transaction prepared with COMP fee');
  
  // 4. Submit to paymaster
  const userOp = await smartAccount.prepareUserOperation({ calls: callsWithFee });
  const sponsoredUserOp = await paymaster.sponsorUserOperation(userOp);
  
  console.log('✅ UserOp sponsored by paymaster');
  
  // 5. Send transaction
  const txHash = await smartAccount.sendUserOperation(sponsoredUserOp);
  console.log(`📤 Transaction sent: ${txHash}`);
  
  // 6. Wait for confirmation
  const receipt = await waitForReceipt(txHash);
  console.log(`✅ Transaction confirmed in block ${receipt.blockNumber}`);
  
  // 7. Verify fee payment
  const treasuryBalance = await checkCOMPBalance(process.env.TREASURY_ADDRESS);
  console.log(`💵 Treasury received fee. New balance: ${treasuryBalance} COMP`);
  
  console.log('\n🎉 E2E Demo Complete!');
}

runE2EDemo().catch(console.error);
```

**Estimated Time:** 3-4 hours  
**Dependencies:** Base Sepolia access, test wallets  
**Risk:** Low

---

# Next Steps

**Ready to start Medium Priority tasks. Which would you like to tackle first?**

1. **Chainlink Oracle** (2-3 hours, most critical)
2. **Monitoring** (4-6 hours, requires infrastructure)
3. **E2E Demo** (3-4 hours, good for validation)

Or continue to **Long-term roadmap items** (WCU, OTR, x402)?
