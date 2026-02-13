# 📉 Cost Plan: Lean Operation for Individual Builder

## 1. Development Phase (Initial Setup Cost)
- **AI Coding Tool:** Using Google tech stack and Cloud Assist (approx. $20/mo)
- **Domain:** Purchase relevant domain like `a2trust.io` (approx. $12/year)
- **Total:** Approx. $30 ~ $40 (One-time and subscription)

## 2. Infrastructure (Operational Cost - Monthly)
### 2.1. Backend & API (Free Tier Maximize)
- **Hosting:** Google Cloud Run (Use within free tier) or Vercel.
- **Database:** Supabase (Free tier: 500MB database).
- **Cost:** $0

### 2.2. Blockchain & Payment
- **Network:** Use Base (Ethereum L2) Mainnet.
- **Gas Fee:** Approx. $0.001 - $0.01 per transaction (**Validated** on Base Mainnet).
- **Strategy:** Developer pays for the first 100 transactions (Paymaster), then included in fees.
- **Cost:** Approx. $10 (Proportional to usage)

### 2.3. AI Model API
- **Model:** Gemini 1.5 Flash (For agent logic processing, low cost/high speed).
- **Cost:** Approx. $10 ~ $20 (For initial testing and agent operation)

## 3. Scalability & Cost Optimization
- **Traffic Spike:** Prevent excessive costs by using Google Cloud Run Auto-scaling.
- **Data Archiving:** Archive old transaction logs from on-chain to off-chain (static files) to reduce DB costs.

## 4. Monthly Total Estimate
- **Minimum Operating Cost:** Approx. $30 ~ $50
- *Cost can be controlled by adjusting API call frequency according to budget.*