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
- [ ] `COMP_PRICE_USD` matches current market/target price
- [ ] `ETH_PRICE_USD` updated to current price
- [ ] `MARKUP_RATE` appropriate for mainnet
- [ ] `ENABLE_COMP_FEES=false` (enable gradually post-deployment)

---

## Deployment Execution

### Step 1: Deploy ComputeToken

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
# Add COMP token address
COMP_TOKEN_ADDRESS=<DEPLOYED_ADDRESS>

# Keep fees disabled initially
ENABLE_COMP_FEES=false

# Other mainnet settings
RPC_URL=https://mainnet.base.org
FEE_TOKEN_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913  # USDC Base
TREASURY_ADDRESS=<YOUR_TREASURY>
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

Update COMP address in TOKEN_ADDRESSES:
```typescript
'COMP': '<DEPLOYED_ADDRESS>',  // Update from Sepolia to Mainnet
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

## Gradual COMP Rollout

### Day 1-2: Internal Testing

```bash
# Enable COMP for your test wallets only
# Feature flag or allowlist in code

# Test COMP fee transactions
# Monitor:
- Fee validation success
- Oracle price accuracy
- Transaction confirmation times
```

- [ ] Internal COMP transactions successful
- [ ] No errors in logs
- [ ] Price oracle working correctly

### Day 3-5: Limited Beta (10% users)

```bash
# Set ENABLE_COMP_FEES=true
# Monitor closely
```

- [ ] COMP adoption rate tracked
- [ ] User feedback collected
- [ ] No failed validations

### Day 6-7: Full Rollout (100%)

```bash
# If all metrics good, enable for all users
```

- [ ] Announce COMP fee support
- [ ] Update documentation
- [ ] Monitor USDC vs COMP ratio

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Fee Validation Rate**
   - Target: > 99% success
   - Alert if < 95%

2. **USDC vs COMP Usage**
   - Track adoption over time
   - Expected: Gradual COMP increase

3. **Service Health**
   - Uptime: > 99.9%
   - Response time: < 500ms p95
   - Error rate: < 0.1%

4. **Oracle Accuracy**
   - ETH/USD price freshness
   - COMP price updates

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
# Disable COMP fees immediately
cd apps/paymaster
echo "ENABLE_COMP_FEES=false" >> .env
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
**COMP Token Address:** _______________  
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

Remember: Start with `ENABLE_COMP_FEES=false`, test thoroughly, then enable gradually.
