# 🚀 Base Mainnet Deployment - Final Checklist

## Pre-Deployment (Complete ALL items)

### 1. Environment Setup ✓

- [ ] Created `.env.mainnet`- [ ] **Environment Configuration (`.env`)**
  - [ ] `DEPLOYER_PRIVATE_KEY` (Funded with ~0.01 ETH)
  - [ ] `TREASURY_ADDRESS` (Cold Wallet)
  - [ ] `TOKEN_NAME` and `TOKEN_SYMBOL` (Define your token identity)
  - [ ] `PAYMASTER_ADDRESS` (If using separate paymaster)
  - [ ] `BASESCAN_API_KEY` (For verification)
- [ ] Verified all addresses are **Base Mainnet** (not Sepolia!)

### 2. Wallet Preparation ✓

- [ ] Deployer wallet funded with >0.01 ETH on Base Mainnet
- [ ] Deployer wallet backed up securely (hardware wallet recommended)
- [ ] Treasury is multi-sig or hardware wallet
- [ ] Team has access to emergency admin keys

### 3. Code Review ✓

- [ ] All tests passing (43/43)
- [ ] Build successful (`pnpm build` in all packages)
- [ ] Code reviewed by team
- [ ] No hardcoded secrets or test data
- [ ] Git commit tagged for deployment

### 4. Configuration Validation ✓

- [ ] `INITIAL_SUPPLY` set appropriately
- [ ] `TOKEN_PRICE_USD` matches current market/target price
- [ ] `ETH_PRICE_USD` updated to current price
- [ ] `MARKUP_RATE` appropriate for mainnet
- [ ] `ENABLE_TOKEN_FEES=false` (enable gradually post-deployment)

---

## Deployment Execution

### Step 1: Deploy UtilityToken

```bash
cd packages/contracts

# Load mainnet environment
source .env.mainnet

# Deploy (with confirmation prompts)
npx hardhat run scripts/deploy-compute-token.ts --network baseMainnet

# OR use safety-checked script
tsx ../scripts/deploy-mainnet.ts
```

**Expected output:**
```
✅ Contract deployed to: 0x...
✅ Admin role granted to: 0x...
✅ Minter role granted to: 0x...
✅ Deployment saved to deployments-mainnet.json
```

**Record the deployed address:** `___________________________________`

### Step 2: Verify on Basescan

```bash
npx hardhat verify --network baseMainnet <DEPLOYED_ADDRESS>
```

**Verification URL:** _______________________________________

### Step 3: Update Paymaster Configuration

Edit `apps/paymaster/.env`:

```bash
# Add TOKEN token address
TOKEN_ADDRESS=0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2

# Keep fees disabled initially
ENABLE_TOKEN_FEES=false

# Other mainnet settings
RPC_URL=https://mainnet.base.org
FEE_TOKEN_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913  # USDC Base
TREASURY_ADDRESS=0x129154b7E3f0Ab0E59615ef578f6511b072FB431
```

### Step 4: Deploy Paymaster Service

```bash
cd apps/paymaster

# Build
pnpm build

# Test locally with mainnet config (dry run)
pnpm start

# Deploy to Cloud Run / your hosting
gcloud run deploy paymaster \
  --source . \
  --region us-central1 \
  --env-vars-file .env
```

### Step 5: Update SDK

Edit `packages/pay-sdk/src/paymaster/paymaster.ts`:

Update TOKEN address in TOKEN_ADDRESSES:
```typescript
'TOKEN': '0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2',  // Update from Sepolia to Mainnet
```

Publish new version:
```bash
cd packages/pay-sdk
pnpm version patch
pnpm build
pnpm publish
```

---

## Post-Deployment Validation

### Immediate Checks (First 15 min)

- [ ] Contract visible on Basescan
- [ ] Contract verified (green checkmark)
- [ ] Admin roles correct (deployer has DEFAULT_ADMIN_ROLE)
- [ ] Minter role granted to paymaster
- [ ] Paymaster service running without errors
- [ ] Health endpoint responding (`curl https://your-paymaster/health`)

### First Hour

- [ ] Test USDC fee validation (existing flow)
- [ ] Submit test UserOp with USDC fee
- [ ] Verify treasury received fee
- [ ] Check paymaster logs for errors
- [ ] Monitor gas usage

### First 24 Hours

- [ ] No service errors or crashes
- [ ] USDC fee success rate > 99%
- [ ] Average response time < 500ms
- [ ] No security alerts

---

## Gradual TOKEN Rollout

### Day 1-2: Internal Testing

```bash
# Enable TOKEN for your test wallets only
# Feature flag or allowlist in code

# Test TOKEN fee transactions
# Monitor:
- Fee validation success
- Oracle price accuracy
- Transaction confirmation times
```

- [ ] Internal TOKEN transactions successful
- [ ] No errors in logs
- [ ] Price oracle working correctly

### Day 3-5: Limited Beta (10% users)

```bash
# Set ENABLE_TOKEN_FEES=true
# Monitor closely
```

- [ ] TOKEN adoption rate tracked
- [ ] User feedback collected
- [ ] No failed validations

### Day 6-7: Full Rollout (100%)

```bash
# If all metrics good, enable for all users
```

- [ ] Announce TOKEN fee support
- [ ] Update documentation
- [ ] Monitor USDC vs TOKEN ratio

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Fee Validation Rate**
   - Target: > 99% success
   - Alert if < 95%

2. **USDC vs TOKEN Usage**
   - Track adoption over time
   - Expected: Gradual TOKEN increase

3. **Service Health**
   - Uptime: > 99.9%
   - Response time: < 500ms p95
   - Error rate: < 0.1%

4. **Oracle Accuracy**
   - ETH/USD price freshness
   - TOKEN price updates

### Alert Thresholds

```yaml
alerts:
  - name: High Fee Validation Failure Rate
    condition: failure_rate > 5%
    action: Page on-call team
    
  - name: Service Down
    condition: uptime < 99%
    action: Immediate page
    
  - name: High Response Time
    condition: p95_latency > 1s
    action: Notify team
```

---

## Rollback Plan

### Quick Rollback (< 5 min)

```bash
# Disable TOKEN fees immediately
cd apps/paymaster
echo "ENABLE_TOKEN_FEES=false" >> .env
pm2 restart paymaster  # or your process manager

# OR revert to previous deployment
gcloud run deploy paymaster --image <previous-image>
```

### Full Rollback (< 30 min)

```bash
# Revert SDK
cd packages/pay-sdk
git checkout v<previous-version>
pnpm build && pnpm publish

# Revert Paymaster
cd apps/paymaster
git checkout <previous-stable-commit>
pnpm build
# Redeploy
```

---

## Emergency Contacts

- **Smart Contract Admin:** _______________________
- **DevOps Lead:** _______________________
- **Security Team:** _______________________
- **On-call Engineer:** _______________________

---

## Success Criteria

✅ Contract deployed and verified  
✅ All roles correctly assigned  
✅ Paymaster service running  
✅ USDC fees working (100% backward compat)  
✅ Monitoring active  
✅ Team notified  

---

## Deployment Record

**Deployment Date:** _______________  
**Deployed By:** _______________  
**TOKEN Token Address:** _______________  
**Paymaster URL:** _______________  
**Git Commit:** _______________  
**Team Approval:** ✓ _______________ (Name/Signature)

---

## Notes / Issues

_Use this space to record any deployment issues, decisions, or observations_

```




```

---

**🎉 Congratulations on your mainnet deployment!**

Remember: Start with `ENABLE_TOKEN_FEES=false`, test thoroughly, then enable gradually.
