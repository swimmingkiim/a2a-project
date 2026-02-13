# Base Mainnet Deployment Checklist

## Pre-Deployment Requirements

### 1. Environment Setup

- [ ] **Deployer Wallet**
  - [ ] Funded with ETH on Base Mainnet
  - [ ] Private key secured in `.env`
  - [ ] Backup wallet address recorded

- [ ] **Contract Configuration**
  ```bash
  DEPLOYER_PRIVATE_KEY=<your-mainnet-deployer-key>
  PAYMASTER_ADDRESS=<your-mainnet-paymaster-address>
  BASE_MAINNET_RPC_URL=https://mainnet.base.org
  BASESCAN_API_KEY=<your-basescan-api-key>
  ```

- [ ] **Smart Contract Audit** (Optional but Recommended)
  - [ ] Security review completed
  - [ ] Known issues documented
  - [ ] Mitigation strategies in place

### 2. Testing Validation

- [ ] All tests passing on testnet
  - [x] UtilityToken: 17/17 ✅
  - [x] Oracle: 15/15 ✅
  - [x] Fee Validators: 7/7 ✅
  - [x] SDK: 4/4 ✅

- [ ] Integration tests completed
- [ ] Load testing performed
- [ ] Edge cases covered

### 3. Monitoring Setup

- [ ] Logging infrastructure ready
- [ ] Alert system configured
- [ ] Metrics dashboard prepared
- [ ] Incident response plan documented

---

## Deployment Steps

### Step 1: Deploy UtilityToken to Base Mainnet

```bash
cd packages/contracts

# Ensure .env is configured for mainnet
# DEPLOYER_PRIVATE_KEY=...
# PAYMASTER_ADDRESS=...
# BASE_MAINNET_RPC_URL=https://mainnet.base.org

# Deploy contract
pnpm hardhat run scripts/deploy-compute-token.ts --network baseMainnet

# Expected output:
# ✅ UtilityToken deployed to: 0x...
# ✅ Admin role granted to: 0x...
# ✅ Minter role granted to: 0x...
```

**Record the deployed address:** `0x________________`

### Step 2: Verify Contract on Basescan

```bash
pnpm hardhat verify --network baseMainnet <DEPLOYED_ADDRESS>

# Verify role assignments
pnpm hardhat run scripts/verify-roles.ts --network baseMainnet
```

### Step 3: Update Paymaster Configuration

**File:** `apps/paymaster/.env`

```bash
# Update TOKEN token address to mainnet deployment
TOKEN_ADDRESS=<MAINNET_DEPLOYED_ADDRESS>

# Set conservative initial price
TOKEN_PRICE_USD=0.10

# Start with TOKEN fees DISABLED
ENABLE_TOKEN_FEES=false

# Update RPC to mainnet
RPC_URL=https://mainnet.base.org

# Ensure treasury and fee token are mainnet addresses
TREASURY_ADDRESS=<YOUR_MAINNET_TREASURY>
FEE_TOKEN_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913  # USDC Base Mainnet
```

### Step 4: Deploy Paymaster Service

```bash
cd apps/paymaster

# Build
pnpm build

# Test locally with mainnet config (dry run)
pnpm start

# Verify logs:
# ✅ Connected to Base Mainnet
# ℹ️  TOKEN fee validation disabled (ENABLE_TOKEN_FEES=false)
# ✅ USDC fee validation active
```

### Step 5: Deploy to Production Environment

**Cloud Run / AWS / Your hosting platform:**

```bash
# Example: Cloud Run
gcloud run deploy paymaster \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="$(cat .env | xargs)"

# Or Docker
docker build -t paymaster:mainnet .
docker run -p 8080:8080 --env-file .env paymaster:mainnet
```

### Step 6: Update SDK Configuration

**File:** `packages/pay-sdk/src/paymaster/paymaster.ts`

Update token addresses for mainnet:

```typescript
const TOKEN_ADDRESSES = {
  'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', // USDC Base Mainnet
  'TOKEN': '<MAINNET_DEPLOYED_ADDRESS>',  // Update this
};
```

Publish new SDK version:

```bash
cd packages/pay-sdk
pnpm version patch  # or minor/major
pnpm build
pnpm publish
```

---

## Post-Deployment Validation

### Immediate Checks (First 15 minutes)

- [ ] **Service Health**
  ```bash
  curl https://your-paymaster-url/health
  # Expected: {"status":"ok","network":"base-mainnet"}
  ```

- [ ] **USDC Fee Validation** (Existing flow)
  - [ ] Submit test transaction with USDC fee
  - [ ] Verify successful validation
  - [ ] Check treasury received fee

- [ ] **Logs Review**
  ```bash
  # Check for errors
  kubectl logs -f paymaster-pod | grep ERROR
  
  # Verify initialization
  kubectl logs paymaster-pod | grep "TOKEN fee validation"
  ```

### First 24 Hours

- [ ] Monitor error rates
- [ ] Track USDC fee validation success rate
- [ ] Verify no regressions in existing flows
- [ ] Check gas usage patterns

### Week 1: Gradual TOKEN Rollout

**Day 1-2: Internal Testing**
- [ ] Enable TOKEN for internal test accounts only
- [ ] Set `ENABLE_TOKEN_FEES=true`
- [ ] Restart service
- [ ] Test TOKEN fee transactions

**Day 3-4: Limited Beta**
- [ ] Enable for 10% of users (feature flag)
- [ ] Monitor TOKEN vs USDC usage ratio
- [ ] Track any failed validations

**Day 5-7: Full Rollout**
- [ ] Enable TOKEN for all users
- [ ] Announce feature launch
- [ ] Monitor metrics closely

---

## Rollback Plan

If issues arise:

### Quick Rollback (< 5 minutes)

```bash
# Disable TOKEN fees immediately
export ENABLE_TOKEN_FEES=false

# Restart service
kubectl rollout restart deployment/paymaster

# Or in .env
echo "ENABLE_TOKEN_FEES=false" >> .env
pnpm start
```

### Full Rollback (< 30 minutes)

```bash
# Revert to previous SDK version
cd packages/pay-sdk
git checkout <previous-version-tag>
pnpm build
pnpm publish --tag rollback

# Revert paymaster service
cd apps/paymaster
git checkout <previous-stable-commit>
pnpm build
# Redeploy
```

---

## Monitoring Metrics

### Key Performance Indicators

1. **Fee Validation Success Rate**
   - Target: > 99%
   - Alert if < 95%

2. **USDC vs TOKEN Usage Ratio**
   - Track adoption rate
   - Expected: Gradual increase in TOKEN usage

3. **Average Response Time**
   - Target: < 500ms
   - Alert if > 1s

4. **Error Rate**
   - Target: < 0.1%
   - Alert if > 1%

### Dashboard Queries

```sql
-- Fee validation breakdown (if using DB logging)
SELECT 
  tokenType,
  COUNT(*) as total,
  SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
  AVG(processingTimeMs) as avg_time
FROM fee_validations
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY tokenType;
```

---

## Security Checklist

- [ ] Private keys never committed to git
- [ ] `.env` files in `.gitignore`
- [ ] Rate limiting enabled
- [ ] SSRF protection active
- [ ] API keys rotated regularly
- [ ] Access logs enabled
- [ ] Audit trail for role changes

---

## Emergency Contacts

- **Smart Contract Admin:** [Contact]
- **DevOps Lead:** [Contact]
- **Security Team:** [Contact]
- **On-call Engineer:** [Rotation]

---

## Success Criteria

✅ Contract deployed and verified  
✅ Service running without errors  
✅ USDC fees working (backward compatibility)  
✅ TOKEN fees functional (when enabled)  
✅ Monitoring active  
✅ Rollback tested  

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Contract Address:** _____________  
**Service URL:** _____________
