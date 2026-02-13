# 🚀 Deployment Plan: A2A Economy Ecosystem (GCP-Native)

## 1. Architecture Overview
- **Compute:** Google Cloud Run (Fully managed serverless)
- **Database:** Cloud SQL for PostgreSQL (Instance: db-f1-micro)
- **Security:** Cloud Secret Manager (For Wallet Private Keys & API Keys)
- **CI/CD:** Cloud Build + Artifact Registry
- **Discovery:** Static `llms.txt` and `agents.md` on Cloud Storage / Root Path

## 2. Phase 1: Infrastructure Setup (Zero to Hero)
1. **Project Init:** Create GCP project and link billing account (Budget Alert $10 required).
2. **Network:** Start with public endpoint without VPC interface configuration (Cost saving).
3. **Database:** - Create Cloud SQL PostgreSQL instance (f1-micro, 10GB storage).
   - Create schemas for `a2trust`, `a2pay`, `a2api`.
4. **Secret:** Store Ethereum L2 (Base) wallet private key in Secret Manager.

## 3. Phase 2: Application Deployment
1. **Containerization:** Build Docker image for FastAPI-based backend.
2. **Cloud Run Deploy:**
   - `--min-instances 0`: Zero cost when no requests.
   - `--max-instances 5`: Prevent costs from unexpected traffic spikes.
   - `--memory 512Mi`: Minimum specs recommended as it focuses on lightweight text processing.
3. **Environment Variables:** Inject DB connection info and API endpoints.

## 4. Phase 3: Agent Optimization (The "Agent-Native" Touch)
1. **Domain Mapping:** Connect custom domain `a10m.work` and verify automatic SSL renewal.
2. **llms.txt Deployment:** Place agent-readable service specification at root path (`/llms.txt`).
3. **Warm-up Policy:** (Optional) Call 'health check' every 15 minutes using Cloud Scheduler if Cold Start delay is a concern (Minimal cost).

## 5. Estimated Monthly Cost (Individual Tier)
- **Cloud Run:** $0 - $2 (Mostly covered within free quota)
- **Cloud SQL:** ~$10 (Based on f1-micro always-on)
- **Secret Manager/Storage:** ~$1
- **Total:** **Approx. $13**