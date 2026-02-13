# AGENTS.md

> **Context & Persona**: You are an expert Web3 & AI Solution Architect contributing to the 'A2A System', a UI-less trust infrastructure for autonomous agents.

## Project Structure
This is a monorepo managed by `pnpm`.
- `/packages`: Shared SDKs and libraries.
    - `/trust-sdk`: DID, VC, ZKP logic (Veramo, Circom).
    - `/pay-sdk`: ERC-7579, Session Keys (Permissionless.js, Viem).
    - `/api-sdk`: MCP implementation, A2A Protocol (TypeScript).
    - `/contracts`: Solidity Smart Contracts (Foundry).
- `/apps`: Deployable services.
    - `/agent-node`: Reference implementation of an autonomous agent.
    - `/registry`: Discovery service server.

## Coding Guidelines
- **Language**: TypeScript (Strict mode enabled).
- **Style**: Functional programming preference. Use extensive JSDoc.
- **Error Handling**: Create custom typed error classes for Protocol/Identity/Payment failures.
- **Documentation**: Maintain this file and `llms.txt` for agent-readability.

## Technology Stack
- **Identity**: @veramo/core, did-jwt-vc, snarkjs.
- **Payment**: viem (v2.x), permissionless.js, ERC-7579.
- **Marketplace**: Model Context Protocol (MCP) SDK, Zod.
- **Infrastructure**: Base L2 (Ethereum), Google Cloud Run.

## Key Principles
1. **Unsupervised Autonomy**: Systems must operate without human intervention.
2. **Verifiable Trust**: All interactions must be cryptographically verifiable.
3. **Interoperability**: Strict adherence to standards (DID, VC, MCP, ERC-4337).
