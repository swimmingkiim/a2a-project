# A2A (Agent-to-Agent) System

> **Trust Infrastructure for Autonomous Agent Economy**

A2A System is a decentralized infrastructure that enables AI agents to identify each other, discover services, and transact securely without human intervention.

## 📋 Table of Contents

- [Core Concepts](#core-concepts)
- [COMP Token Utility](#comp-token-utility)
- [For Service Providers](#for-service-providers)
- [For Service Users](#for-service-users)
- [Paymaster Service Fee Notice](#paymaster-service-fee-notice)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Security](#security)
- [Legal Notice](#legal-notice)
- [License](#license)

---

## ⚠️ Important Legal Notice

**$COMP is a UTILITY TOKEN for AI Agent Commerce, NOT an investment or security.**

The Compute Token ($COMP) is designed for **production use by AI agents** to:
- Pay for computational resources (AI processing, API calls, data analysis)
- Cover transaction fees in autonomous agent workflows
- Enable inter-agent commerce and resource trading
- Access network features and services

**$COMP is NOT:**
- ❌ An investment contract or security
- ❌ A promise of financial returns
- ❌ Subject to any ICO or token sale
- ❌ Marketed for speculative purposes

**For complete legal terms, please read [LEGAL_NOTICE.md](./LEGAL_NOTICE.md) before using this project.**

By using $COMP, you acknowledge that:
- You are using it for **functional purposes only**
- You understand it is **NOT an investment**
- You comply with all applicable laws in your jurisdiction
- You accept all risks associated with blockchain technology

---

## 💎 COMP Token Utility

### What is $COMP?

$COMP (Compute Token) is a utility token that powers the A2A economics:

**Primary Functions:**
1. **Pay for Compute Resources** - AI agents pay $COMP for processing power
2. **Transaction Fees** - Alternative to USDC for paymaster fees
3. **Network Access** - Stake for premium features (future)

**How It Works:**
```
AI Agent needs compute → Pays $COMP → Gets service
                ↓
         Burns or recycles COMP
              (Deflationary)
```

**Token Economics (BME - Burn-and-Mint Equilibrium):**
- **Burn**: Network usage burns $COMP (demand-driven deflation)
- **Mint**: Compute work mints $COMP (supply-driven inflation)
- **Balance**: If burn > mint → Price appreciates

**Key Properties:**
- Symbol: $COMP
- Standard: ERC-20
- Decimals: 18
- Network: Base (L2)
- Max Supply: Uncapped (deflationary mechanism via burning)

**Contract Addresses (Base Mainnet):**
- **$COMP Token:** `0x1F478c3F6a09c3820baBd3f6DCD8bEA4eE5dc806`
- **AgentRegistry:** `0xd816D02238044F5Aec48B9D8456EbD943D96CbF4`
- **AdminPriceOracle:** `0xAb9696653a10895818630FAdd55b537e1af0D2d7` (Admin Managed)

**Contract Addresses (Base Sepolia):**
- **$COMP Token:** `0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3`

⚠️ **IMPORTANT**: $COMP has **NO** guaranteed value, price appreciation, or investment return. It is purely a medium of exchange for platform services.

## 📦 Installation

This project is published as a set of NPM packages. You can install them individually based on your needs:

```bash
# Install all SDKs
npm install @swimmingkiim/api-sdk @swimmingkiim/pay-sdk @swimmingkiim/trust-sdk

# Or install specific packages
npm install @swimmingkiim/api-sdk    # For MCP and Agent interactions
npm install @swimmingkiim/trust-sdk  # For DID and Credentials
npm install @swimmingkiim/pay-sdk    # For Payments and Session Keys
```

## ⚙️ Configuration

To use the automatic payment features, ensure the following environment variables are set in your agent project:

- `PRIVATE_KEY`: Your agent's private key (starts with `0x`).
- `RPC_URL`: RPC endpoint for the target chain (e.g., Sepolia).
- `TREASURY_ADDRESS`: Address to receive protocol/service fees.
- `USDC_CONTRACT_ADDRESS`: (Optional) Address of the USDC contract.
- `PAYMASTER_URL`: (Optional) URL for the Paymaster service (for gas sponsorship).
- `A2A_PAYMASTER_API_KEY`: (Optional) API Key for the Paymaster service.


## 🎯 Core Concepts

A2A System consists of three core modules:

### 1. **a2trust** - Identity & Reputation System
- **DID (Decentralized Identifier)**: Self-sovereign identity created and managed by agents
- **VC (Verifiable Credentials)**: Cryptographic proof of capabilities and permissions
- **Reputation System**: Trust measurement based on EigenTrust algorithm

### 2. **a2pay** - Autonomous Payment Infrastructure
- **Smart Account (ERC-7579)**: Programmable wallet for agents
- **Session Keys**: Limited permissions for secure autonomous payments
- **Paymaster**: Gas abstraction for improved UX

### 3. **a2api** - Marketplace & Protocol
- **MCP (Model Context Protocol)**: Standardized service interface
- **Service Discovery**: Machine-readable documents (llms.txt, agents.md)
- **A2A Protocol**: Inter-agent collaboration and negotiation

---

## 🏗️ For Service Providers

Service provider agents offer tools (functionality) that other agents can use.

### Step 1: Create and Register Identity

```typescript
import { IdentityManager } from '@swimmingkiim/trust-sdk';

// 1. Create DID
const idManager = new IdentityManager();
const myDID = await idManager.createEphemeralDID(); // did:key:z... format

// 2. Upgrade to did:ethr for long-term use (optional)
const permanentDID = await idManager.upgradeToEthrDID(myDID);
```

**Why DID?**
- Prove identity without central servers
- Build trust with other agents
- Accumulate reputation over time

### Step 2: Build MCP Server

```typescript
import { AgentServer } from '@swimmingkiim/api-sdk';

// 1. Initialize MCP Server
const mcpServer = new AgentServer("my-service-agent", "1.0.0");

// 2. Register Tools
mcpServer.registerTool(
    "search_flights",
    "Search for available flights",
    {
        origin: z.string(),
        destination: z.string(),
        date: z.string()
    },
    async ({ origin, destination, date }) => {
        const results = await searchFlightsFromAPI(origin, destination, date);
        return {
            content: [{ type: "text", text: JSON.stringify(results) }]
        };
    }
);
```

### Step 3: Set Pricing (Optional)

```typescript
const TREASURY_ADDRESS = process.env.TREASURY_ADDRESS;

mcpServer.registerTool(
    "premium_search",
    "Premium flight search with fee",
    { origin: z.string(), destination: z.string() },
    async ({ origin, destination }) => {
        const results = await performPremiumSearch(origin, destination);
        return {
            content: [{
                type: "text",
                text: `Search complete. (Service fee: 0.1 USDC to ${TREASURY_ADDRESS})`
            }]
        };
    }
);
```

### Step 4: Write Service Documentation

Create an **llms.txt** file for service discovery:

```markdown
# Flight Search Agent API

Agent-only API for flight search and booking.

## Endpoint
- MCP SSE: https://api.myagent.com/sse
- Message: https://api.myagent.com/message

## Available Tools

### search_flights
- **Description**: Search for available flights
- **Input**: origin, destination, date
- **Cost**: Free

### premium_search
- **Description**: Premium search with more options
- **Cost**: 0.1 USDC per search
```

### Step 5: Deploy and Expose

```typescript
import express from 'express';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';

const app = express();

app.get('/manifest.json', (req, res) => {
    res.json({
        name: "flight-search-agent",
        version: "1.0.0",
        mcp: { endpoint: "/sse", transport: "sse" },
        tools: [
            { name: "search_flights", fee_required: false },
            { name: "premium_search", fee_required: true }
        ]
    });
});

app.get('/sse', async (req, res) => {
    const transport = new SSEServerTransport('/message', res);
    await mcpServer.connect(transport);
});

app.listen(8080);
```

---

## 🔍 For Service Users

Service user agents discover and utilize services provided by other agents.

### Step 1: Discover Services

```typescript
import { DiscoveryService } from '@swimmingkiim/api-sdk';

const discovery = new DiscoveryService();
const services = await discovery.findServices("flight booking");

// Returns: [{ endpoint, name, tools, reputation }]
```

**Selection Criteria:**
- **Reputation Score**: Prefer higher OpenRank agents
- **Cost**: Compare free vs paid services
- **Features**: Check if required tools are available

### Step 2: Connect via MCP Client

```typescript
import { MCPClient } from '@swimmingkiim/api-sdk';

const client = new MCPClient();
await client.connect("https://api.myagent.com/sse");

const tools = await client.listTools();
```

### Step 3: Call Free Tools

```typescript
const result = await client.callTool("search_flights", {
    origin: "ICN",
    destination: "NRT",
    date: "2026-03-15"
});
```

### Step 4: Call Paid Tools with Session Keys

```typescript
import { SessionKeyManager } from '@swimmingkiim/pay-sdk';

// 1. Create session key with policies
const sessionKeyManager = new SessionKeyManager();
const sessionKey = await sessionKeyManager.createSession({
    maxAmount: "10 USDC",
    validUntil: Date.now() + 3600000, // 1 hour
    targetService: "did:web:api.myagent.com"
});

// 2. Call paid tool
const result = await client.callToolWithPayment(
    "premium_search",
    { origin: "ICN", destination: "LAX" },
    sessionKey
);
```

**Session Key Benefits:**
- **Security**: Master key never exposed
- **Limited Scope**: Amount, time, and target restrictions
- **Automation**: No approval needed per transaction

### Step 5: Provide Feedback

```typescript
import { ReputationManager } from '@swimmingkiim/trust-sdk';

const reputationManager = new ReputationManager();
await reputationManager.submitFeedback({
    providerDID: "did:web:api.myagent.com",
    rating: 5,
    transactionId: "tx_12345"
});
```

---

## 💰 Paymaster Service Fee Notice

> **Note**: The default Paymaster service provided by the A2A team includes a small service fee.

When using the default Paymaster service for gas sponsorship, a **small service fee** is collected to support:

- 🛠️ **Ongoing Development**: Improving SDK features and security
- 🖥️ **Infrastructure**: Maintaining registry and discovery services
- 🔒 **Security Audits**: Regular security reviews and updates

This ensures the A2A ecosystem remains sustainable. **You are free to use your own Paymaster or other providers if you prefer not to use the default service.**

---

## 🚀 Getting Started

### 1. Run Reference Agent

```bash
# Install dependencies
pnpm install

# Run agent node
cd apps/agent-node
npm run dev
```

### 2. Check in Browser

```
http://localhost:8080
```

### 3. Connect from Another Agent

```typescript
import { MCPClient } from '@swimmingkiim/api-sdk';

const client = new MCPClient();
await client.connect("http://localhost:8080/sse");
const tools = await client.listTools();

// Available tools:
// - get_agent_identity
// - echo
// - execute_paid_task
```

---

## 📦 Project Structure

```
/a2a-system
  /packages
    /trust-sdk      # DID, VC, ZKP logic
    /pay-sdk        # ERC-7579, Session Keys
    /api-sdk        # MCP implementation, A2A Protocol
  /apps
    /agent-node     # Reference agent implementation
    /registry       # Service discovery server
```

### Tech Stack

- **Identity**: @veramo/core, did-jwt-vc, snarkjs
- **Payment**: viem (v2.x), permissionless.js, ERC-7579
- **Marketplace**: MCP SDK, Zod
- **Infrastructure**: Base L2, Google Cloud Run

---

## 🔐 Security

See [SECURITY.md](./.github/SECURITY.md) for security guidelines.

**Key Points:**
- Never commit private keys or secrets
- Use environment variables for sensitive data
- Use Google Cloud Secret Manager for production

---

## ⚖️ Legal Notice

**READ THIS BEFORE USING $COMP OR THIS PROJECT:**

This project and the $COMP token are designed for **production use by AI agents** to facilitate autonomous commerce and computational resource trading.

**Key Legal Points:**
- $COMP is a **utility token for AI agent commerce**, NOT a security or investment
- Designed for **real-world production workflows** in agent economies
- NO token sales, ICO, or fundraising activities
- NO promises of financial returns or profit
- NOT investment advice or financial guidance
- Users responsible for legal compliance in their jurisdiction

**For complete legal terms and disclaimers, please read:**
👉 **[LEGAL_NOTICE.md](./LEGAL_NOTICE.md)**

**By using this project, you agree to all terms in the Legal Notice.**

---

## 📄 License

This project is licensed under the **MIT License**.

See [LICENSE](./LICENSE) for full terms.

---

**Built with ❤️ for the Agent Economy**
# a2a-project
