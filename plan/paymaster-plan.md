# Technical Specification: A2A Paymaster Gateway (Managed Gas Abstraction)

> **Context**: This document provides the technical roadmap for building a "Paymaster Gateway" on Google Cloud Run.
> **Goal**: To move beyond a simple proxy by creating an intelligent infrastructure layer that handles gas sponsorship, security enforcement, and automated revenue generation for the A2A ecosystem.

---

## 🤖 AI Development Role

You are a **Senior Web3 & Security Engineer**. Your objective is to implement the "A2A Paymaster Gateway," a secure middleware that abstracts blockchain gas complexities for AI agents while ensuring the financial integrity of the service.

---

## 🏗️ System Architecture: The Gateway Model

### 1. High-Level Logic

The Gateway acts as an intelligent router between AI Agents and upstream providers (e.g., Pimlico).

1. **Request Verification**: 
   - Authenticate the agent via DID and check for valid Verifiable Credentials (VC).
   - **Solvency Check (Critical):** Before sponsoring gas, the gateway performs an on-chain balanceOf check to ensure the agent actually holds sufficient $COMP tokens. This prevents 'Empty Wallet' attacks.
2. **L1 Fee Safety**: 
   - For Base L2, query the L1 Fee Oracle (`0x4200...000F`) to include data posting costs.
   - Oracle queries include L1 data fee buffers to prevent Paymaster from operating at a loss on Optimism stack chains.
3. **Markup Engine**: Apply a service fee (e.g., 10%) to the estimated gas to cover infrastructure costs and generate revenue for the **Community Treasury**.
4. **Proxy Forwarding**: Forward the sanitized and signed `UserOperation` to the upstream provider.

### 2. Deployment & Domain Strategy

* **Service URL**: `paymaster.a10m.work`
* **Infrastructure**: Google Cloud Run with Custom Domain Mapping.

---

## ⚙️ Configuration & Environment Variables

The AI must ensure all sensitive keys are retrieved from **Google Cloud Secret Manager**.

| Variable | Description | Source |
| --- | --- | --- |
| `UPSTREAM_PAYMASTER_URL` | URL of the provider actually sponsoring gas (Pimlico/Alchemy). | Secret Manager |
| `RPC_URL` | Base L2 Node RPC for L1 Fee Oracle calls. | Secret Manager |
| `MARKUP_RATE` | Percentage added to gas (e.g., 0.1 for 10%). | Env Variable |
| `TREASURY_ADDRESS` | Destination wallet for the collected markup fees. | Env Variable |
| `A2A_PAYMASTER_API_KEY` | Key used by the SDK to authenticate with the Gateway. | Secret Manager |

---

## 🛡️ Security Implementation & Guardrails

To mitigate financial and technical risks, the following must be implemented:

* **SSRF Prevention**: Strict allowlisting of `UPSTREAM_PAYMASTER_URL`. Block all internal/local IP ranges.
* **Rate Limiting**: Enforce a maximum number of sponsorship requests per DID and per IP address to prevent "Gas Griefing" attacks.
* **Simulation Verification**: Use `eth_estimateUserOperationGas` before forwarding to ensure the transaction will not fail, protecting the Gateway from paying for reverted txs.
* **Regulatory Compliance**: Position the service as **"Infrastructure-as-a-Service (IaaS)"** rather than a financial transmitter. Fees are for "Gas Calculation and Security Routing".

---

## 🧪 Security Test Cases (Quality Assurance)

The AI should generate the following tests to verify Gateway integrity:

### 1. Authorization & Identity

* **[FAIL] Unauthorized DID**: Submit a request with a DID that lacks the required gas-sponsorship VC. Expect `403 Forbidden`.
* **[FAIL] Invalid API Key**: Submit a request with a missing or incorrect `A2A_PAYMASTER_API_KEY`. Expect `401 Unauthorized`.

### 2. Protection Against Malicious Requests

* **[FAIL] SSRF Attempt**: Change the `UPSTREAM_PAYMASTER_URL` in the config to `http://127.0.0.1:8080`. The Gateway should block the request.
* **[FAIL] Gas Griefing**: Flood the Gateway with valid requests from a single DID. Verify that Rate Limiting triggers after the threshold.
* **[FAIL] Forged UserOp Signature**: Submit a UserOperation where the signature does not match the sender. The simulation step should catch this and reject the request.

### 3. Financial Accuracy

* **[PASS] Markup Verification**: Verify that the response `paymasterAndData` contains a gas limit that is exactly `(Actual_Estimate * (1 + MARKUP_RATE))`.
* **[PASS] L1 Fee Inclusion**: Compare a standard L2 estimate with the Gateway response. Ensure the Gateway response is higher, reflecting the L1 Data Fee calculation.

### 4. Resilience

* **[FAIL] Upstream Timeout**: Simulate the Upstream Provider being down. Ensure the Gateway returns a graceful `504 Gateway Timeout` and logs the incident.