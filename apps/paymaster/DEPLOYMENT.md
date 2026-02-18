# Paymaster Production Deployment Guide

## Pre-Flight Checklist ✈️

Before deploying to Base Mainnet, verify all items below:

### Environment Configuration

- [ ] `NODE_ENV=production` is set
- [ ] `CI` is **unset** or set to `false` (CRITICAL)
- [ ] `DISABLE_PAYMASTER=false`
- [ ] `MARKUP_RATE >= 1.5` for gas volatility protection
- [ ] All token addresses are for **Base Mainnet**:
  - `USDC_TOKEN_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
  - `DAIM_ADDRESS=0x...` (Your deployed token)
  - `TREASURY_ADDRESS=0x...` (Your treasury)

### Wallet Funding

- [ ] Paymaster signer wallet has **>= 0.01 ETH**
- [ ] Treasury can receive USDC and your project tokens
- [ ] Test transaction from signer wallet works

### Infrastructure

- [ ] RPC URL configured (Alchemy/Infura/QuickNode)
- [ ] Upstream Paymaster URL configured (Pimlico)
- [ ] Database connection tested (if using dynamic API keys)
- [ ] Load balancer/reverse proxy configured
- [ ] SSL/TLS certificates installed

---

## Deployment Steps

### 1. Environment Setup

Copy production template:

```bash
cd apps/paymaster
cp .env.production.example .env
```

Edit `.env` and fill in all values. **Critical variables:**

```bash
NODE_ENV=production
CI=  # MUST be empty or false!
DISABLE_PAYMASTER=false

# Base Mainnet Addresses
USDC_TOKEN_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
DAIM_ADDRESS=0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2  // DaimToken on Base Mainnet
TREASURY_ADDRESS=0x129154b7E3f0Ab0E59615ef578f6511b072FB431    // Your treasury

# Safety Settings
MARKUP_RATE=1.5           # Recommended: 1.5-2.0
MIN_SIGNER_BALANCE_ETH=0.01

# RPC (use production-grade provider)
RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR-KEY
UPSTREAM_PAYMASTER_URL=https://api.pimlico.io/v2/base/rpc?apikey=YOUR-KEY

# Funding Wallet (keep secret!)
PAYMASTER_SIGNER_PRIVATE_KEY=0x...
```

### 2. Validate Configuration

Run validation check:

```bash
npm run build
node dist/index.js
```

**Expected output:**
```
✅ Production environment validation passed
Paymaster Service running on port 8080
Network: https://base-mainnet.g.alchemy.com/v2/...
```

**If you see:**
```
🚨 FATAL: CI=true is set in production mode!
```

→ **STOP!** Unset `CI` before proceeding!

### 3. Fund Paymaster Wallet

Send ETH to the address derived from `PAYMASTER_SIGNER_PRIVATE_KEY`:

```bash
# Get signer address (run in Node.js)
node -e "
const { Wallet } = require('ethers');
const wallet = new Wallet(process.env.PAYMASTER_SIGNER_PRIVATE_KEY);
console.log('Signer Address:', wallet.address);
"
```

Send **0.05 ETH initially** to this address on Base Mainnet.

### 4. Deploy to Production

#### Option A: Docker

```bash
# Build image
docker build -t paymaster:latest -f apps/paymaster/Dockerfile .

# Run container
docker run -d \
  --name paymaster \
  --env-file apps/paymaster/.env \
  -p 8080:8080 \
  paymaster:latest
```

#### Option B: Cloud Run (GCP)

```bash
# Build and deploy
gcloud builds submit --config cloudbuild.yaml

# Set environment variables via console or:
gcloud run services update paymaster \
  --set-env-vars=NODE_ENV=production,MARKUP_RATE=1.5,...
```

#### Option C: PM2 (VPS)

```bash
npm run build
pm2 start dist/index.js --name paymaster -i max
pm2 save
```

### 5. Verify Deployment

**Health check:**

```bash
curl https://your-domain.com/health
```

**Expected response:**

```json
{
  "status": "ok",
  "timestamp": "2026-02-11T00:00:00.000Z",
  "version": "1.0.0",
  "environment": "production",
  "emergencyShutdown": false
}
```

**Test sponsorship request:**

```bash
curl -X POST https://your-domain.com/v1/paymaster \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "method": "pm_sponsorUserOperation",
    "params": [...]
  }'
```

---

## Post-Deployment Monitoring

### Critical Logs to Watch (First 24 Hours)

Monitor these log patterns in your container/server logs:

#### 1. Insufficient Balance Warnings

```
[USDC Validator] ❌ INSUFFICIENT BALANCE!
  Sender: 0x...
  Has: 50000 USDC
  Needs: 100000 USDC
```

**Meaning:** Defense working correctly. User tried to pay without funds.  
**Action:** None. This is expected behavior.

#### 2. L1 Fee Calculation Errors

```
[USDC Validator] ❌ L1 Fee calculation failed: ...
```

**Meaning:** RPC node issue or network problem.  
**Action:**
- If **frequent** (>10% of requests): Switch RPC provider
- If **rare** (<1% of requests): Monitor only

#### 3. Emergency Shutdown Triggered

```
🚨 [EMERGENCY] Paymaster is disabled. Rejecting request.
```

**Meaning:** `DISABLE_PAYMASTER=true` was set (manual intervention).  
**Action:** Investigate why shutdown was triggered.

### Monitoring Metrics

Set up alerts for:

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| Signer ETH Balance | < 0.01 ETH | **URGENT**: Top up immediately |
| Request Error Rate | > 5% | Check RPC provider |
| Balance Check Failures | > 50/hour | Possible attack - review logs |
| Health Check Down | Any failure | Service restart needed |

### Recommended Monitoring Tools

- **Logs**: CloudWatch, Stackdriver, or Datadog
- **Metrics**: Prometheus + Grafana
- **Alerts**: PagerDuty, OpsGenie, or Slack webhooks

---

## Emergency Procedures

### Scenario 1: Unexpected Fund Drainage

**Symptoms:**
- Signer wallet ETH dropping rapidly
- Treasury not receiving expected fees

**Immediate Actions:**

1. **Emergency Shutdown:**

```bash
# Set in .env or via environment
export DISABLE_PAYMASTER=true

# Or restart with flag
DISABLE_PAYMASTER=true npm start
```

2. **Check logs for suspicious patterns:**

```bash
grep "INSUFFICIENT BALANCE" logs/* | wc -l
# If this number is LOW, balance checks are being bypassed!
```

3. **Verify CI mode is OFF:**

```bash
echo $CI  # Should be empty or "false"
```

### Scenario 2: RPC Provider Outage

**Symptoms:**
- L1 Fee calculation failures spike
- Health check still passes but requests fail

**Actions:**

1. Switch RPC provider immediately:

```bash
export RPC_URL=https://backup-rpc-provider.com
# Restart service
```

2. Consider multi-RPC setup with automatic failover

### Scenario 3: Gas Price Spike

**Symptoms:**
- Treasury collecting fees but losing money
- Paymaster balance dropping despite fee collection

**Actions:**

1. **Temporarily increase markup:**

```bash
export MARKUP_RATE=2.5  # Increase from 1.5 to 2.5
# Restart service
```

2. Monitor for 1 hour, adjust as needed

---

## Security Hardening

### Production-Only Settings

1. **Restrict CORS origins:**

```typescript
// apps/paymaster/src/index.ts
app.use(cors({
    origin: ['https://your-frontend.com'], // Whitelist only
    allowedHeaders: ['Content-Type', 'x-api-key']
}));
```

2. **Rate limiting (already implemented):**

Configured via `RATE_LIMIT_RPM` environment variable.

3. **API Key rotation:**

Periodically rotate static API keys:

```bash
A2A_PAYMASTER_API_KEY=$(openssl rand -hex 32)
```

### Backup Wallet

Keep a backup signer private key in a secure vault. If main wallet is compromised:

1. Set `DISABLE_PAYMASTER=true`
2. Drain remaining ETH from compromised wallet
3. Update `PAYMASTER_SIGNER_PRIVATE_KEY` to backup
4. Re-enable service

---

## Rollback Procedure

If issues arise:

1. **Revert to previous version:**

```bash
# Docker
docker pull paymaster:previous-tag
docker stop paymaster
docker run -d --name paymaster paymaster:previous-tag

# PM2
git checkout previous-commit
npm run build
pm2 restart paymaster
```

2. **Enable emergency shutdown temporarily:**

```bash
DISABLE_PAYMASTER=true
```

3. **Investigate logs before re-enabling**

---

## Performance Tuning

### Recommended Instance Specs

- **CPU**: 2 vCPUs minimum
- **RAM**: 2GB minimum
- **Disk**: 10GB SSD
- **Network**: Low latency to RPC provider

### Auto-Scaling (Cloud Run)

```yaml
# cloudbuild.yaml
--min-instances=1
--max-instances=10
--concurrency=100
```

---

## Support Checklist

Before contacting support, gather:

- [ ] Last 100 lines of logs
- [ ] Environment configuration (redact secrets!)
- [ ] Health check response
- [ ] Signer wallet balance
- [ ] Treasury wallet balance
- [ ] RPC provider status
- [ ] Timestamp of issue

---

## Success Indicators

After deployment, you should see:

✅ Health endpoint returns `"status": "ok"`  
✅ Signer balance stable or increasing  
✅ Treasury receiving fee transfers  
✅ <1% error rate on requests  
✅ Response times < 2 seconds  

---

## Next Steps

Once stable in production:

1. Set up monitoring dashboards
2. Configure automated alerts
3. Schedule weekly wallet balance reviews
4. Document incident response procedures
5. Plan for scaling (additional regions, load balancing)

**Congratulations! Your Paymaster is production-ready. 🚀**
