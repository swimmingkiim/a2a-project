# Project Roadmap & TODOs

Based on the analysis of `plan/service.md`, `plan/bussiness-model.md`, and `plan/cost-plan.md`, this document outlines the step-by-step plan to build the A2A (Agent-to-Agent) Trust & Payment Ecosystem.

## 🚀 Phase 0: Project Initialization & Scaffolding
- [x] **Monorepo Setup**: Initialize project using pnpm workspaces (or Turborepo) complying with the `service.md` structure.
    - Structure: `/packages` (sdk), `/apps` (services).
- [x] **Environment Setup**: Configure TypeScript (Strict), ESLint, Prettier.
- [x] **Master Prompt Integration**: Create `AGENTS.md` (or `agents.md`) to guide future agent interactions.

## 🆔 Phase 1: a2trust (Identity & Reputation Layer)
- [x] **DID Setup**:
    - Implement `did:key` for ephemeral sessions.
    - Implement `did:ethr` (Base L2) for persistent identity.
    - Use `@veramo/core` and `@veramo/did-provider-ethr`.
- [x] **Verifiable Credentials (VC)**:
    - Implement VC signing and verification using `did-jwt-vc`.
    - Define schemas for "Identity Verification" and "Authorization/Mandate".
- [ ] **Privacy (ZKP)**:
    - Setup `snarkjs` and `circom` basic integration for selective disclosure.
- [ ] **Reputation System**:
    - Design interfaces for EigenTrust/OpenRank integration.

## 💳 Phase 2: a2pay (Autonomous Payment Layer)
- [x] **Core Setup**: Install `viem` (v2.x) and `permissionless.js`.
- [x] **Smart Account Implementation**:
    - Scaffold `packages/pay-sdk`.
    - Implement Modular Smart Account support (ERC-7579).
- [ ] **Session Keys (Critical)**:
    - **[Immediate Task]** Implement `SessionKeyManager` class.
    - Create `createSessionKey()`: Generate ephemeral key pair.
    - Create `enableSession()`: Create UserOp for session enablement.
    - Create `executeWithSession()`: Execute transactions via Bundler.
    - Implement Policy validation (Time-bound, Value Limit, Target Restriction).
- [ ] **Paymaster Integration (Paymaster Proxy)**:
    - [x] **[Immediate]** Remove legacy SDK usage fee logic from `agent-node`.
    - [x] **[Immediate]** Scaffold `apps/paymaster` service (Express/TS).
    - [x] Implement `POST /v1/paymaster` JSON-RPC handler.
    - [ ] Integrate with upstream providers (Pimlico/Base) and handle L1 fee calculation.
    - [x] Update `pay-sdk` to use the new Proxy.
- [ ] **Network Configuration**: Base Sepolia / Base Mainnet.

## 🌐 Phase 3: a2api (Marketplace & Connection Layer)
- [x] **MCP Implementation**:
    - Setup Model Context Protocol (MCP) TypeScript SDK.
    - Implement Server capability for tools/resources discovery.
- [ ] **Discovery Service**:
    - Implement `DiscoveryService` to parse and validate `llms.txt`.
    - Create Zod schemas for Agent Card registry.
- [ ] **Google A2A Integration**:
    - Implement high-level handshake/negotiation logic interoperable with Google's A2A protocol.

## 🤖 Phase 4: Applications & Reference Implementation
- [x] **Agent Node (`apps/agent-node`)**:
    - Create a reference implementation of an autonomous agent using the SDKs.
- [ ] **Registry Service (`apps/registry`)**:
    - Build a simple server for agent discovery.

## ☁️ Infrastructure & Ops (Cost Plan Alignment)
- [x] **Cloud Setup**: Prepare Google Cloud Run configuration (Auto-scaling).
- [ ] **Database**: Setup Supabase for off-chain data (logs, non-critical state).
- [ ] **Cost Optimization**: Ensure API calls leverage caching to stay within `cost-plan.md` estimates.

---
**Note**: Tasks should be executed sequentially, starting from Phase 0.
