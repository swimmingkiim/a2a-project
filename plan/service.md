# **A2A (Agent-to-Agent) Trust Ecosystem Architecture and Infrastructure In-Depth Research Report for AI Agents**

## **1\. Introduction: The Advent of the M2M Economy and the Necessity of Trust Infrastructure**

### **1.1 Paradigm Shift from Human-Centric Internet to Agent-Centric Economy**

The landscape of the digital economy is changing rapidly. While the internet of the past 30 years was centered on Graphical User Interfaces (GUI) optimized for Human-to-Human or Human-to-Computer interactions, the advancement of Generative AI and Large Language Models (LLM) is driving the rise of 'Agentic AI' equipped with autonomous decision-making and execution capabilities.1 Software is now evolving beyond tools into subjects of economic activity, inevitably heralding the era of the M2M Economy where machines directly exchange value and collaborate.

Agentic AI is different from simple automation scripts. They understand ambiguous goals, establish multi-step plans, and find and execute necessary tools on their own.2 According to McKinsey's analysis, such agent-based organizations have the potential to exponentially improve organizational productivity by drastically reducing legacy middleware and API integration costs and autonomously orchestrating complex workflows between systems.1 However, current web infrastructure is not suitable for these agents to operate. Existing security models relying on human visual verification and trust (CAPTCHA, 2FA, etc.) act as barriers hindering agent autonomy, and centralized platform dependency prevents free movement and combination between agents.

Therefore, a new form of 'UI-less' trust infrastructure is essential for agents to process tens of thousands of transactions per second and collaborate across borders and platforms. This infrastructure must include **Identity** for agents to identify each other, **Payment** to safely transfer value, and **Marketplace** protocols to discover and negotiate necessary services.

### **1.2 Key Components and Design Philosophy of the A2A Ecosystem**

The A2A (Agent-to-Agent) trust ecosystem proposed in this report consists of three complementary modules: 'a2trust', 'a2pay', and 'a2api'.

1. **a2trust (Identity & Reputation):** Decentralized Identity (DID) and reputation system where agents can prove their identity and verify mutual reliability without a centralized certification authority.
2. **a2pay (Autonomous Payment):** Programmable payment infrastructure that can safely manage funds while minimizing human approval procedures. Account Abstraction and Session Key technologies are key.
3. **a2api (Marketplace & Protocol):** A network for discovering and binding services through Machine-Readable Documentation that agents can read and understand, and standardized communication protocols (MCP, A2A Protocol).

The design philosophy of this system is 'Unsupervised Autonomy' and 'Verifiable Trust'. Agents operate freely without human intervention within predefined Policies, but all actions must be cryptographically proven and traceable.

## ---

**2\. a2trust: Decentralized Identity (DID) and Verifiable Credentials (VC) Based Identity Architecture**

### **2.1 Analyzing Decentralized Identifiers (DID) Methodology for Autonomous Agents**

The first problem to solve in the agent economy is identifying "Who is this agent?". Traditional email or OAuth-based authentication relies on centralized service providers, risking agent platform dependency or identity loss upon service verification. The W3C DID standard was designed to solve this.3 DID is an identifier generated and controlled by the agent based on a cryptographic Key Pair, propagating the public key and service endpoint via a DID Document registered on a blockchain or distributed ledger.4

Suitable DID methods vary depending on agent characteristics (lifespan, transaction frequency, security requirements), and the A2A ecosystem adopts a hybrid approach through the following comparative analysis.

| DID Method | Technical Mechanism | Pros | Cons & Limitations | A2A Application Scenario |
| :---- | :---- | :---- | :---- | :---- |
| **did:key** | Derived directly from public key (Deterministic generation) | \- No separate Ledger needed \- Instant generation (Zero-latency) \- Cost 0 (Gas-free) | \- Key Rotation impossible \- Revocation impossible \- Difficult to accumulate long-term reputation 5 | 'Disposable Agent' performing one-time tasks or short-term session identification |
| **did:ethr** | Ethereum address or Smart Contract based | \- Inherits strong security of Ethereum ecosystem \- Supports Key Rotation & Delegation \- Easy direct integration with Smart Contracts | \- Gas fee for DID Document update \- Slow transaction speed on Mainnet 5 | 'Primary Agent' holding financial assets or needing to build long-term reputation |
| **did:web** | DID Document hosting via DNS domain and HTTPS | \- High compatibility using existing web infrastructure (DNS) \- Advantageous for large organization/enterprise identity proof | \- Centralized dependency on DNS admin \- Security vulnerability upon domain hijacking 5 | 'Enterprise Agent' representing a company or institution (e.g., official CS agent of a specific mall) |
| **did:pkh** | Public Key Hash based (CAIP-10) | \- Easy Multi-chain support \- Can use existing wallet addresses | \- Functional limitations similar to did:key | Proving asset ownership in cross-chain environments |

a2trust fundamentally proposes a **hybrid model of did:ethr (L2 based) and did:key**. The agent's master identity is managed by did:ethr on low-cost L2 networks like Base or Arbitrum to ensure persistence, while did:key is used for individual work sessions or short-term communication to maximize efficiency.5

### **2.2 Authority Delegation System via Verifiable Credentials (VC)**

After identity identification, one must prove "What authority does this agent have?". a2trust implements this using the W3C Verifiable Credentials (VC) Data Model.7 A VC is a digital version of a physical ID or certificate, containing the Issuer's electronic signature, making it tamper-proof.

In the A2A ecosystem, VCs are used for two main purposes: 'Attestation' and 'Delegation'.

1. **Attestation (Identity Verification):** Proves attributes like "This agent is an official service agent of Samsung Electronics" or "This agent represents a user with a credit score of 800+".  
2. **Delegation (Authorization):** Acts as a 'Mandate' proving that the user has delegated authority to the agent to perform specific actions.

#### **2.2.1 VC Schema and JSON-LD Structure Design**

For interoperability between agents, VCs must be structured in JSON-LD (JSON for Linking Data) format which machines can understand.8 Below is an example schema of a 'Payment Authority Delegation' VC that can be used in the A2A ecosystem.

JSON

{  
  "@context": \[  
    "https://www.w3.org/2018/credentials/v1",  
    "https://a2trust.io/contexts/v1"  
  \],  
  "type":,  
  "issuer": "did:ethr:0xUserMasterKey...",  
  "issuanceDate": "2026-02-05T10:00:00Z",  
  "expirationDate": "2026-02-05T12:00:00Z",  
  "credentialSubject": {  
    "id": "did:key:zAgentSessionKey...",  
    "delegationScope": {  
      "allowedAction": "Transfer",  
      "currency": "USDC",  
      "maxAmount": "100.00",  
      "targetService": "did:web:travel-agency.com"  
    }  
  },  
  "proof": {  
    "type": "EcdsaSecp256k1Signature2019",  
    "created": "2026-02-05T10:00:00Z",  
    "proofPurpose": "assertionMethod",  
    "verificationMethod": "did:ethr:0xUserMasterKey\#controller",  
    "jws": "eyJhbGciOiJFUzI1NiIs..."  
  }  
}

In this structure, credentialSubject refers to the authorized agent (did:key), and delegationScope clearly limits the scope of actions the agent can perform. When a service provider agent (Verifier) receives this VC, it looks up the Issuer's public key in the DID Document to verify the signature and automatically checks if the delegationScope matches the requested action.8

#### **2.2.2 Enhancing Privacy with Zero-Knowledge Proofs (ZKP)**

When agents handle sensitive information, they often need to prove validity without exposing the original data. For example, a medical scheduling agent proving "Eligible for specialist consultation" without revealing the specific diagnosis of the patient, or a financial agent proving "Holds balance sufficient for payment" while hiding the exact balance amount.11

a2trust integrates ZKP functionality into VCs using Circom and SnarkJS libraries. It implements Selective Disclosure using cryptographic techniques like 'BBS+ Signatures' or 'AnonCreds'.9 This prevents data leakage at the source by allowing agents to transfer only the minimum necessary information to the counterparty.

### **2.3 EigenTrust Algorithm Based Decentralized Reputation System**

In an open network where anonymous agents operate, quantifying 'trust' is essential. It is necessary to prevent malicious agents from disrupting the network or low-quality agents from demanding high prices. a2trust introduces the **EigenTrust Algorithm** developed at Stanford University to solve this.12

#### **2.3.1 Principle of EigenTrust Algorithm**

EigenTrust mathematically models Transitive Trust: "Peers trusted by trusted peers are trustworthy".

1. **Local Trust Value (![][image1]):** Score evaluated by agent ![][image2] after trading with agent ![][image3]. Calculated as the difference between satisfactory transactions (![][image4]) and unsatisfactory transactions (![][image5]), and normalized.  
   ![][image6]  
   ![][image7]  
2. **Global Trust Value (![][image8]):** Trustworthiness of agent ![][image2] across the entire network. This converges to the Left Eigenvector of the trust matrix $C \= \[c\_{ij}\]$.  
   ![][image9]

Through this iterative calculation, a global reputation score is derived for all agents in the network.13

#### **2.3.2 Integration of OpenRank and Karma3 Labs Protocols**

In real implementations, it is inefficient for all agents to perform full matrix operations. Therefore, a2trust utilizes off-chain computing protocols like **OpenRank**.14 OpenRank collects social graph data from Farcaster or Lens Protocol and on-chain transaction data to perform EigenTrust computations and provides the results (reputation scores) in a verifiable form.15

In the A2A ecosystem, service provider agents can present their OpenRank score in the form of a VC. For example, they can charge higher service fees or be selected preferentially by user agents by proving qualifications like "Top 5% OpenRank Tier".17 This provides resistance against Sybil Attacks or Collusion attacks and induces self-purification of the ecosystem.13

## ---

**3\. a2pay: Autonomous Financial Infrastructure via Account Abstraction and Smart Session Keys**

### **3.1 Financial Layer Requirements and Existing Limitations for AI Agents**

Existing blockchain wallets (EOA, Externally Owned Account) are unsuitable for AI agents. There is a risk of losing all assets if the Private Key is leaked, needing to hold gas fees (ETH) for every transaction, and inability to implement complex logic (e.g., auto-transfer, limit setting).19 a2pay grants programmable financial authority to agents based on Ethereum's **Account Abstraction (ERC-4337)** standard.

### **3.2 ERC-7579 Modular Smart Account Architecture**

ERC-7579 is a standard that ensures interoperability by modularizing smart account functions.20 a2pay follows this standard to allow agents to assemble financial functions like LEGO blocks.

| Module Type | Function | A2A Application Example |
| :---- | :---- | :---- |
| **Validators** | Logic validating transaction validity | Session key signature verification, Biometric (on user approval) verification 20 |
| **Executors** | Module executing transactions on behalf of the account | Auto-transfer of subscription fees, Execute trade when specific condition (price reached) is met 22 |
| **Hooks** | Execute specific logic before/after transaction | Daily spending limit check, Block transaction upon anomaly detection 20 |
| **Fallback Handlers** | Handle undefined calls | Maintain compatibility with existing assets 20 |

This modular structure allows agents to upgrade functions without creating a new account as they evolve. For example, a 'Multisig' module or 'Social Recovery' module can be added to an agent that initially had only simple transfer functions to enhance security.23

### **3.3 Smart Session Keys and Access Control Policies**

The core security mechanism of a2pay is **Session Keys**.24 Users generate a temporary Key Pair (Session Key Pair) using their Master Key (Owner Key) and sign a VC containing a specific Policy for this key and deliver it to the agent. The agent generates transactions using this session key, but the Smart Account (Validator module) executes it only after verifying that the transaction does not violate the policy.25

**Session Key Policy Detailed Design:**

* **Time-bound:** Sets the validity period of the key via validAfter and validUntil timestamps (e.g., "Valid only for the next 1 hour").
* **Value Limit:** Limits the maximum amount of ETH/ERC-20 tokens usable during a specific period (e.g., "Max 10 USDC usable").
* **Target Restriction:** Whitelists interactable smart contract addresses and Function Selectors (e.g., "Only callable to exactInputSingle function of Uniswap V3 Router").25

SDKs like ZeroDev or Rhinestone provide tools to serialize these permission policies and verify them on-chain and off-chain.28 This ensures that even if an agent is hacked, the damage is limited to the scope assigned to that session key.

### **3.4 Gas Abstraction and Cost Analysis Using Paymaster**

It is inefficient for agents to secure ETH and calculate gas fees every time they send a transaction. ERC-4337's **Paymaster** allows third parties to pay gas fees on behalf of the user.30

* **Sponsorship Paymaster:** Service provider fully subsidizes user's gas fees to improve user experience (Web2 style).
* **Token Paymaster:** Allows users to pay gas fees with ERC-20 tokens like USDC, DAI. The Paymaster accepts these and exchanges them for ETH on DEX to pay the network.31

#### **3.4.1 Cost Efficiency Analysis: L2 Network Comparison**

Low-cost networks are essential to handle frequent transactions of AI agents. A comparative analysis of gas fees and characteristics of major L2 networks as of 2025 is as follows.32

| Network | Avg Transaction Cost | Throughput (TPS) | Agent Suitability Analysis |
| :---- | :---- | :---- | :---- |
| **Arbitrum One** | \~$0.01 \- $0.02 | 40,000+ (Stylus applied) | Suitable for financial agents requiring complex DeFi computations. Reasonable billing based on resource usage with Dynamic Pricing.35 |
| **Base** | \~$0.001 \- $0.005 | 2,000+ | Optimized for commercial agents with frequent fiat deposits/withdrawals due to integration with Coinbase ecosystem. Provides lowest cost efficiency.34 |
| **Solana** | \< $0.0005 | 65,000+ | Although lacking Ethereum compatibility, an alternative choice for cases requiring ultra-high speed/ultra-low cost like massive data transactions or IoT agents.32 |

a2pay adopts **Base Network** as the base layer considering compatibility and stability, but takes a multi-chain strategy considering expansion to Arbitrum or Solana when high performance is needed. Also, operating costs for AI agents (inference costs, etc.) are dropping rapidly due to model performance improvements and hardware advancements 36, so the proportion of transaction fees in total costs will become increasingly important.

## ---

**4\. a2api: Marketplace Protocol for Agent Communication and Service Discovery**

### **4.1 Service Standardization Based on Model Context Protocol (MCP)**

AI agents need a standardized interface to interact with the outside world. The **Model Context Protocol (MCP)**, proposed by Anthropic and released as open source, acts like a 'USB-C' connecting AI models and data/tools.37 a2api requires all registered agents to comply with the MCP server standard.

#### **4.1.1 MCP Architecture and Lifecycle**

MCP consists of Host (LLM Application), Client (Connection Module), and Server (Tool Provider).39

1. **Initialization:** When Client and Server connect, they negotiate protocol version and Capabilities via initialize request.41
2. **Discovery:** Server delivers a list of Resources (Read-only data, e.g., files, logs), Prompts (Predefined templates), and Tools (Executable functions) it provides to the Client.
3. **Operation & Sampling:** When the Agent (Client) requests tool execution (tools/call), the Server performs it and returns the result. If necessary, it also supports sampling where the Server requests LLM generation from the Client.43

This structure allows agents to dynamically grasp and use functions at runtime without learning the counterparty's API documentation in advance.

### **4.2 Comparison and Integration with Google Agent2Agent (A2A) Protocol**

Google's **Agent2Agent (A2A) Protocol** is similar to MCP but focuses more on 'Collaboration between Agents'.44 While MCP has strengths in 'Tool Connection', A2A specializes in long-term task delegation, negotiation, and task management between agents.

| Feature | MCP (Model Context Protocol) | A2A (Agent2Agent Protocol) |
| :---- | :---- | :---- |
| **Primary Purpose** | Connecting LLM with external data/tools (Context & Tools) | Collaboration and task coordination between agents (Collaboration) |
| **Communication Method** | JSON-RPC 2.0 (Mostly local/tunneling) 43 | HTTP/HTTPS, SSE (Web standard based) 45 |
| **Key Functions** | Read resources, Execute tools, Provide prompts | Capability discovery (Agent Card), Negotiation, Long-term task management |
| **Application Point** | Function extension of single agent (Tool layer of a2api) | Workflow orchestration between agents (Collaboration layer of a2api) |

a2api combines the strengths of both protocols. It adopts a hierarchical structure using A2A Protocol for high-level negotiation (price, schedule, etc.) between agents 46, and MCP for calling specific functions in the actual service execution phase.

### **4.3 Machine-Readable Documentation: llms.txt and agents.md**

It is inefficient and error-prone for agents to scrape and understand HTML documents meant for humans. The a2api ecosystem mandates standardized documentation for agents.

1. **llms.txt:** Located at /llms.txt path of the website, providing service overview, key document links, and API spec summaries in markdown format.47 Just as robots.txt is for search engine crawlers, llms.txt acts as a sitemap for AI agents.49
2. **agents.md (or agent.md):** Located at the project or repository root, specifying rules (coding style, build commands, test procedures, etc.) that agents must follow when analyzing code or performing tasks.51 This reduces 'onboarding' time when developer agents (Devin, Claude Code, etc.) are deployed to the project.53

**llms.txt Example:**

# **A2A Travel Service API**

This service is an Agent-only API for flight search and booking.

## **Core Resources**

\-([https://api.a2a.travel/docs.md](https://api.a2a.travel/docs.md)): Full Endpoint Specification

* [Pricing Model](https://api.a2a.travel/pricing.md): Agent Billing Policy

## **Optional**

* [Changelog](https://api.a2a.travel/changelog.md): Change History
  50

Such machine-readable documents play a crucial role in reducing token consumption and increasing accuracy when agents perform RAG (Retrieval-Augmented Generation).54

## ---

**5\. Service Plan: A2A System \- UI-less Autonomous Economy Operating System**

### **5.1 System Overview and Architecture**

**A2A System** is an infrastructure enabling agents to conduct economic activities without human intervention. This system has no visual UI (Headless), and all interactions occur via APIs and Smart Contracts.

* **Target Users:** Autonomous Agent Developers, AI Assistant Service Providers, IoT Device Manufacturers.
* **Core Value:** Zero-Friction (Minimized human intervention), Verifiable Trust (Mathematical trust), Interoperability (Standards-based compatibility).

**Architecture Diagram (Text Description):**

\[Application Layer\]  
Agent A (Consumer) \<--- (A2A Protocol / HTTP) \---\> Agent B (Provider)

| |  
       v                                                v  
\[Interface Layer: a2api\]  
MCP Client \<------- (JSON-RPC) \-------\> MCP Server (Tools & Resources)  
Discovery Service (llms.txt Reader)     Agent Card Registry

| |  
       v                                                v

DID Resolver (Veramo)                   Modular Smart Account (Kernel/Safe)  
VC Verifier (ZKP)                       Session Key Validator  
Reputation Oracle (OpenRank)            Paymaster (Gas Sponsorship)

| |  
       v                                                v  
\[Infrastructure Layer\]  
Base L2 / Arbitrum (Blockchain)         IPFS / Arweave (Data Storage)

### **5.2 Key Functional Requirements**

1. **Auto-Identity Issuance and Management:**
   * Auto-generate did:key and register to registry upon agent instantiation.
   * Support did:ethr upgrade and key rotation for long-term agents.
2. **One-Transaction Payment Delegation:**
   * User issues a VC containing session key and spending limit (e.g., 100 USDC) to the agent with a single signature.
   * Agent performs autonomous payments within the limit without additional signatures thereafter.
3. **Dynamic Service Binding:**
   * Convert natural language queries (e.g., "Find me the cheapest GPU cloud") into MCP tool calls.
   * Auto-match optimal provider from a2api registry based on reputation score (EigenTrust).
4. **Verifiable Reputation Feedback:**
   * Submit agent-signed feedback (VC) to on-chain/off-chain reputation system after transaction completion.
   * Reputation score update and automatic blocking of malicious agents (Slashing).

### **5.3 Business Model and Revenue Structure**

A2A System generates revenue as an infrastructure provider.

1. **Protocol Fee:** Collect 0.05% of transaction amount for inter-agent payments via a2pay (Possible due to low L2 gas fees).
2. **Premium Registry (Listing Fee):** Subscription fee for top exposure in a2api marketplace and 'Verified Agent' badge.
3. **Reputation Data API (Data Monetization):** Paid API provision to financial/insurance agents requiring advanced reputation data (EigenTrust Score details).

## ---

**6\. Developer Master Prompt: Integrated Environment Setup for Cursor/Windsurf**

This section is an optimized master prompt that developers can use when building the A2A ecosystem using AI-powered IDEs (Cursor, Windsurf). This prompt clearly instructs project structure, library versions, and coding conventions to reduce hallucinations and speed up implementation.

### **\[Master Prompt\] A2A Ecosystem Development Setup**

**Context & Persona:**

You are an expert Web3 & AI Solution Architect. You are tasked with building the 'A2A System', a UI-less trust infrastructure for autonomous agents. The system consists of a2trust (Identity), a2pay (Payment), and a2api (Marketplace).

**Project Structure:**

Create a monorepo with the following structure:

/a2a-system  
  /packages  
    /trust-sdk      \# DID, VC, ZKP logic (Veramo, Circom)  
    /pay-sdk        \# ERC-7579, Session Keys (Permissionless.js, Viem)  
    /api-sdk        \# MCP implementation, A2A Protocol (TypeScript)  
    /contracts      \# Solidity Smart Contracts (Foundry)  
  /apps  
    /agent-node     \# Reference implementation of an autonomous agent  
    /registry       \# Discovery service server

**Technical Constraints & Libraries:**

1. **Identity (/trust-sdk):**  
   * Use @veramo/core and @veramo/did-provider-ethr for DID management.  
   * Implement VC signing/verification using did-jwt-vc.  
   * Use snarkjs for ZKP proof generation (e.g., range proof for balance).  
2. **Payment (/pay-sdk):**  
   * Use viem (v2.x) for Ethereum interaction.  
   * Use permissionless.js for ERC-4337 and ERC-7579 implementation.  
   * Implement Session Keys using @rhinestone/module-sdk or ZeroDev's session key libraries.  
   * Target Network: Base Sepolia (Testnet) / Base Mainnet.  
3. **Marketplace (/api-sdk):**  
   * Implement Model Context Protocol (MCP) using the official TypeScript SDK.  
   * Create a strictly typed DiscoveryService that parses llms.txt.  
   * Use zod for runtime schema validation of Agent Cards.

**Coding Guidelines:**

* **Language:** TypeScript (Strict mode enabled).  
* **Style:** Functional programming preference. Use extensive JSDoc.  
* **Error Handling:** Create custom typed error classes for Protocol/Identity/Payment failures.  
* **Documentation:** Generate agents.md in the root explaining the codebase to other AI agents.

**Immediate Task:**

Generate the scaffolding for packages/pay-sdk. specifically focusing on a SessionKeyManager class. This class should:

1. Create an ephemeral key pair.  
2. Construct an ERC-7579 compliant "Enable Session" UserOperation.  
3. Accept a Policy object (maxAmount, validUntil, targetAddress).  
4. Include a method to execute a transaction using the active session key via a Bundler.

Please provide the implementation code for SessionKeyManager.ts and the corresponding types definition.

## ---

**7\. Conclusion**

The A2A trust ecosystem is a blueprint for implementing a safe and reliable agent economy while minimizing human intervention. a2trust's DIDs and VCs prove the existence and authority of agents, a2pay's account abstraction and session keys enable autonomous financial activities, and a2api's MCP and machine-readable documents drastically reduce communication costs between agents.

Technologically, the combination of low costs of L2 blockchains, privacy of ZKP, and intelligence of LLMs increases the feasibility of such a system. The A2A System will operate as a foundational infrastructure for various fields such as IoT, supply chain management, and personalized AI assistant services in the future, accelerating the era of the true M2M economy.

#### **References**

1. The agentic organization: A new operating model for AI | McKinsey, Accessed Feb 5, 2026, [https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era](https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era)  
2. Building the Infrastructure for the AI Agent Economy | by Constellation Network \- Medium, Accessed Feb 5, 2026, [https://medium.com/constellationlabs/building-the-infrastructure-for-the-ai-agent-economy-2ffe03221c0b](https://medium.com/constellationlabs/building-the-infrastructure-for-the-ai-agent-economy-2ffe03221c0b)  
3. Decentralized Identifiers (DIDs) v1.0 \- W3C, Accessed Feb 5, 2026, [https://www.w3.org/TR/did-1.0/](https://www.w3.org/TR/did-1.0/)  
4. AI Agents Need Decentralized Identity: Why DID Matters Now \- ArcBlock\!, Accessed Feb 5, 2026, [https://www.arcblock.io/content/blog/ai-agents-need-decentralized-identity-why-did-matters-now](https://www.arcblock.io/content/blog/ai-agents-need-decentralized-identity-why-did-matters-now)  
5. Comparing Decentralized Identifiers(DID) Methods \- DEV Community, Accessed Feb 5, 2026, [https://dev.to/lymah/comparing-decentralized-identifiersdid-methods-el](https://dev.to/lymah/comparing-decentralized-identifiersdid-methods-el)  
6. AI Agents with Decentralized Identifiers and Verifiable Credentials \- arXiv, Accessed Feb 5, 2026, [https://arxiv.org/html/2511.02841v1](https://arxiv.org/html/2511.02841v1)  
7. Verifiable Credentials: The Ultimate Guide 2025 \- Dock Labs, Accessed Feb 5, 2026, [https://www.dock.io/post/verifiable-credentials](https://www.dock.io/post/verifiable-credentials)  
8. Verifiable Credentials Data Model v2.0 \- W3C, Accessed Feb 5, 2026, [https://www.w3.org/TR/vc-data-model-2.0/](https://www.w3.org/TR/vc-data-model-2.0/)  
9. Five Things You Need to Know About JSON-LD Credentials in Hyperledger Aries Cloudagent Python \- Indicio.tech, Accessed Feb 5, 2026, [https://indicio.tech/blog/five-things-you-need-to-know-about-json-ld-credentials-in-hyperledger-aries-cloudagent-python/](https://indicio.tech/blog/five-things-you-need-to-know-about-json-ld-credentials-in-hyperledger-aries-cloudagent-python/)  
10. Verifiable Credential Rendering Methods v1.0 \- W3C, Accessed Feb 5, 2026, [https://www.w3.org/TR/vc-render-method/](https://www.w3.org/TR/vc-render-method/)  
11. Verifiable Credentials Explained | Curity Identity Server, Accessed Feb 5, 2026, [https://curity.io/resources/learn/verifiable-credentials/](https://curity.io/resources/learn/verifiable-credentials/)  
12. EigenTrust \- Wikipedia, Accessed Feb 5, 2026, [https://en.wikipedia.org/wiki/EigenTrust](https://en.wikipedia.org/wiki/EigenTrust)  
13. The EigenTrust Algorithm for Reputation Management in P2P Networks \- Stanford NLP Group, Accessed Feb 5, 2026, [https://nlp.stanford.edu/pubs/eigentrust.pdf](https://nlp.stanford.edu/pubs/eigentrust.pdf)  
14. OpenRank Protocol, Accessed Feb 5, 2026, [https://docs.openrank.com/the-reputation-stack/openrank-protocol](https://docs.openrank.com/the-reputation-stack/openrank-protocol)  
15. Creating your first reputation graph | OpenRank, Accessed Feb 5, 2026, [https://docs.openrank.com/openrank-sdk/creating-your-first-reputation-graph](https://docs.openrank.com/openrank-sdk/creating-your-first-reputation-graph)  
16. Ranking Strategies on Lens | OpenRank, Accessed Feb 5, 2026, [https://docs.openrank.com/integrations/lens-protocol/ranking-strategies-on-lens](https://docs.openrank.com/integrations/lens-protocol/ranking-strategies-on-lens)  
17. Decentralized Reputation Protocol \- OpenRank, Accessed Feb 5, 2026, [https://openrank.com/consumer-apps](https://openrank.com/consumer-apps)  
18. Using Trust and Reputation for Detecting Groups of Colluded Agents in Social Networks \- IEEE Xplore, Accessed Feb 5, 2026, [https://ieeexplore.ieee.org/iel8/6287639/6514899/10815731.pdf](https://ieeexplore.ieee.org/iel8/6287639/6514899/10815731.pdf)  
19. Account Abstraction (ERC-4337), Part 2: Implementation | by Kurt Merbeth \- Medium, Accessed Feb 5, 2026, [https://medium.com/@Kurt0x/account-abstraction-erc-4337-part-2-implementation-d377f1cf0d97](https://medium.com/@Kurt0x/account-abstraction-erc-4337-part-2-implementation-d377f1cf0d97)  
20. ERC-7579: The Complete Guide to Modular Smart Accounts | Eco Support Center, Accessed Feb 5, 2026, [https://eco.com/support/en/articles/11890018-erc-7579-the-complete-guide-to-modular-smart-accounts](https://eco.com/support/en/articles/11890018-erc-7579-the-complete-guide-to-modular-smart-accounts)  
21. ERC-7579, Accessed Feb 5, 2026, [https://erc7579.com/](https://erc7579.com/)  
22. How to use an ERC-7579 compatible smart account with permissionless.js | Pimlico Docs, Accessed Feb 5, 2026, [https://docs.pimlico.io/guides/how-to/accounts/use-erc7579-account](https://docs.pimlico.io/guides/how-to/accounts/use-erc7579-account)  
23. Modular Smart Accounts at Haust Network | by Roberto \- Medium, Accessed Feb 5, 2026, [https://medium.com/@andreysokolow2025/modular-smart-accounts-at-haust-network-9567cf332fd7](https://medium.com/@andreysokolow2025/modular-smart-accounts-at-haust-network-9567cf332fd7)  
24. Session Keys \- Rhinestone, Accessed Feb 5, 2026, [https://docs.rhinestone.dev/home/concepts/session-keys](https://docs.rhinestone.dev/home/concepts/session-keys)  
25. Session Keys \- ZeroDev docs, Accessed Feb 5, 2026, [https://docs.zerodev.app/sdk/advanced/session-keys](https://docs.zerodev.app/sdk/advanced/session-keys)  
26. Session Keys are the JWTs of Web3 \- ZeroDev docs, Accessed Feb 5, 2026, [https://docs.zerodev.app/blog/session-keys-are-the-jwts-of-web3](https://docs.zerodev.app/blog/session-keys-are-the-jwts-of-web3)  
27. Permissions (Session Keys) \- ZeroDev docs, Accessed Feb 5, 2026, [https://docs.zerodev.app/sdk/permissions/intro](https://docs.zerodev.app/sdk/permissions/intro)  
28. erc7579/smartsessions \- GitHub, Accessed Feb 5, 2026, [https://github.com/erc7579/smartsessions](https://github.com/erc7579/smartsessions)  
29. Tutorial \-- Transaction Automation \- ZeroDev docs, Accessed Feb 5, 2026, [https://docs.zerodev.app/smart-wallet/permissions/transaction-automation](https://docs.zerodev.app/smart-wallet/permissions/transaction-automation)  
30. Developer's Guide to ERC-4337 \#5 | Developing a Paymaster | by Nikhil | Block Magnates, Accessed Feb 5, 2026, [https://blog.blockmagnates.com/developers-guide-to-erc-4337-5-developing-a-paymaster-6ce61ef5630f](https://blog.blockmagnates.com/developers-guide-to-erc-4337-5-developing-a-paymaster-6ce61ef5630f)  
31. Account Abstraction Part 2: Sponsoring Transactions Using Paymasters \- Alchemy, Accessed Feb 5, 2026, [https://www.alchemy.com/blog/account-abstraction-paymasters](https://www.alchemy.com/blog/account-abstraction-paymasters)  
32. Unraveling Gas Fees: A Comprehensive Guide to Transaction Costs Across Blockchains, Accessed Feb 5, 2026, [https://medium.com/@ankitacode11/unraveling-gas-fees-a-comprehensive-guide-to-transaction-costs-across-blockchains-72509f649811](https://medium.com/@ankitacode11/unraveling-gas-fees-a-comprehensive-guide-to-transaction-costs-across-blockchains-72509f649811)  
33. GAS vs ARB: Comparing Transaction Costs and Performance Across Ethereum Layer 2 Solutions \- Gate.com, Accessed Feb 5, 2026, [https://www.gate.com/crypto-wiki/article/gas-vs-arb-comparing-transaction-costs-and-performance-across-ethereum-layer-2-solutions-20260116](https://www.gate.com/crypto-wiki/article/gas-vs-arb-comparing-transaction-costs-and-performance-across-ethereum-layer-2-solutions-20260116)  
34. Base vs Arbitrum: Which Ethereum L2 Is Better? \- Arch Lending, Accessed Feb 5, 2026, [https://archlending.com/blog/base-vs-arbitrum](https://archlending.com/blog/base-vs-arbitrum)  
35. Smarter Gas Fees on Arbitrum With Dynamic Pricing, Accessed Feb 5, 2026, [https://blog.arbitrum.io/dynamic-pricing-explainer/](https://blog.arbitrum.io/dynamic-pricing-explainer/)  
36. AI Agent Cost-Based Pricing, Accessed Feb 5, 2026, [https://nevermined.ai/blog/ai-agent-cost-based-pricing](https://nevermined.ai/blog/ai-agent-cost-based-pricing)  
37. Building Intelligent AI Agents with MCP: A Complete Guide to the Model Context Protocol | by Harshal Dhandrut | Medium, Accessed Feb 5, 2026, [https://medium.com/@harshal.dhandrut/building-intelligent-ai-agents-with-mcp-a-complete-guide-to-the-model-context-protocol-5507069068fb](https://medium.com/@harshal.dhandrut/building-intelligent-ai-agents-with-mcp-a-complete-guide-to-the-model-context-protocol-5507069068fb)  
38. Model Context Protocol, Accessed Feb 5, 2026, [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)  
39. The Agent Economy Is Coming: A Plain-English Guide to How AI Will Shop, Negotiate, and Pay on Your Behalf | by Michael J. Goldrich \- Medium, Accessed Feb 5, 2026, [https://medium.com/@michael.goldrich/the-agent-economy-is-coming-a-plain-english-guide-to-how-ai-will-shop-negotiate-and-pay-on-your-fa005decc883](https://medium.com/@michael.goldrich/the-agent-economy-is-coming-a-plain-english-guide-to-how-ai-will-shop-negotiate-and-pay-on-your-fa005decc883)  
40. Unlocking AWS Knowledge with MCP: A Complete Guide to Model Context Protocol and the MCPraxis…, Accessed Feb 5, 2026, [https://ashishkasaudhan.medium.com/unlocking-aws-knowledge-with-mcp-a-complete-guide-to-model-context-protocol-and-the-mcpraxis-597663eb451c](https://ashishkasaudhan.medium.com/unlocking-aws-knowledge-with-mcp-a-complete-guide-to-model-context-protocol-and-the-mcpraxis-597663eb451c)  
41. A Survey of Agent Interoperability Protocols: Model Context Protocol (MCP), Agent Communication Protocol (ACP), Agent-to-Agent Protocol (A2A), and Agent Network Protocol (ANP) \- arXiv, Accessed Feb 5, 2026, [https://arxiv.org/html/2505.02279v1](https://arxiv.org/html/2505.02279v1)  
42. Model Context Protocol (MCP): AI Integration Guide | Medium \- Michiel Horstman, Accessed Feb 5, 2026, [https://michielh.medium.com/the-model-context-protocol-mcp-step-by-step-connecting-ai-agents-to-everything-6b25a052b87c](https://michielh.medium.com/the-model-context-protocol-mcp-step-by-step-connecting-ai-agents-to-everything-6b25a052b87c)  
43. Specification \- Model Context Protocol, Accessed Feb 5, 2026, [https://modelcontextprotocol.io/specification/2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18)  
44. Announcing the Agent2Agent Protocol (A2A) \- Google for Developers Blog, Accessed Feb 5, 2026, [https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)  
45. Google's Agent2Agent Protocol Explained for Enterprise AI Teams, Accessed Feb 5, 2026, [https://galileo.ai/blog/google-agent2agent-a2a-protocol-guide](https://galileo.ai/blog/google-agent2agent-a2a-protocol-guide)  
46. Getting Started with Agent2Agent (A2A) Protocol: A Purchasing Concierge and Remote Seller Agent Interactions on Cloud Run and Agent Engine | Google Codelabs, Accessed Feb 5, 2026, [https://codelabs.developers.google.com/intro-a2a-purchasing-concierge](https://codelabs.developers.google.com/intro-a2a-purchasing-concierge)  
47. Working with llms.txt | Platform Overview \- Mastercard Developers, Accessed Feb 5, 2026, [https://developer.mastercard.com/platform/documentation/agent-toolkit/working-with-llmstxt/](https://developer.mastercard.com/platform/documentation/agent-toolkit/working-with-llmstxt/)  
48. What is llms.txt? Breaking down the skepticism \- Mintlify, Accessed Feb 5, 2026, [https://www.mintlify.com/blog/what-is-llms-txt](https://www.mintlify.com/blog/what-is-llms-txt)  
49. Announcing Twilio Docs Support for llms.txt and Markdown, Accessed Feb 5, 2026, [https://www.twilio.com/en-us/blog/developers/docs-llms-txt-markdown-support](https://www.twilio.com/en-us/blog/developers/docs-llms-txt-markdown-support)  
50. llms-txt: The /llms.txt file, Accessed Feb 5, 2026, [https://llmstxt.org/](https://llmstxt.org/)  
51. This repository defines AGENT.md, a standardized format that lets your codebase speak directly to any agentic coding tool. \- GitHub, Accessed Feb 5, 2026, [https://github.com/agentmd/agent.md](https://github.com/agentmd/agent.md)  
52. AGENTS.md, Accessed Feb 5, 2026, [https://agents.md/](https://agents.md/)  
53. How to write a great agents.md: Lessons from over 2,500 repositories \- The GitHub Blog, Accessed Feb 5, 2026, [https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)  
54. Effective context engineering for AI agents \- Anthropic, Accessed Feb 5, 2026, [https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)  
55. Context Engineering for Multi-Agent LLM Code Assistants Using Elicit, NotebookLM, ChatGPT, and Claude Code \- arXiv, Accessed Feb 5, 2026, [https://arxiv.org/html/2508.08322](https://arxiv.org/html/2508.08322)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAYCAYAAAD6S912AAABpklEQVR4AeyTPShFYRjHj6+BRWSQAVmEQZFBSpQyGJgoxaCQlKwWyYQyyOJjwICUbGJBlEVGX/lYLYqNhPj933uf47hF92C8+v/e//Oce97/fc9zj2Tvn/8SgX8faGKGboa5rC1QA6kQSsEZZrNzETagALphE0LJArPYtQs5UAtTUAXVEOqUFjjOxlLogVeQ5ljawPpMap0a+6J8ulZwUqBu7KLTCW9xk065ZQ1eDBUQKz1FkV1UYCVNChzATzriwz6I1RoXxsBJgS+u8rzrqActL9roV5+g1huAOWWwDsAkpIOTAo+pHkAzxHxpfit05aA5aTQKpnUaZl0FjaIJd1LgE1U79MIM6Bt38BJohDdYgGbQdcxLYlmHO9DIznAnBarYZimEaZiFBhiBZziBOtBIrnDpnUVPptNp/uf0ThaoRptPKS5BGzBfHVRLMAiaHeakL9qn8u8PBnL9W+nRyvhU/oibFLhnjTzewH5uHoVlkNJYNMd6XO8vFlG8gbr7Xgt0gn4cvZMKu6D3FSbQNh1SCL2/Cqf91G8Cb9g+BPNg/+eUEX0AAAD//3zbkr0AAAAGSURBVAMAr5RFMYWgyWsAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAXCAYAAADHhFVIAAAA1UlEQVR4AbSOvwtBURTHH9ktSpn8A1IGg8Uq2RiUhUGy+ZuYFTJTCpOSyWZGmUykfL731en5kcl7nc8959zPu/eeqPfj+5+M8EocYuC9X5tiswdp+JAFNuvwVc4QHZjDy0m9pWcWiAeYzNEUoQ1ZcKE/E1QN0KQtchNcSOrUnm4NuvpGdiF5ohpBGSSHZBeSW6oL6LoNWT3Js4EydHkYgE5XyCZLNHcYQxVUmzyyoUFq5CQsweSUpgs76MMVTJ5pJrCCA7jQtK5g0bWC0o+g9HcCa0jyCQAA///CCpLFAAAABklEQVQDABRKIS8zWosKAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAYCAYAAAAoG9cuAAAA+UlEQVR4AcySsY4BURiFZ3eL7bbZfYdN8AAKCa2IghCNQqURhUdQaFSiEK1EoZAo9BIqCo1EqddKJCIa3/mLmzFjEiU5370z5374xXx6L7zeRNIYFcb9B0832oNkKCZQhkhpy2ENehApnTgcwRlC0gdlGlLgRnEXlN8wBc3TZR+CxS91aMbQhj0UweKXvmhmoCRZdmDxSy1rPO+XPQ4rsPglK1g0uH7AkmvLM0mDXzldgyVKknAxgyUo/dElYAEuQUlfpXlCUpO3VEEpsRxhAy76pD53edA/XmCvww1cJA24+4EcxGAOD5HUoMmCHo0DeyiSQmWweEm6AwAA//+pvVhJAAAABklEQVQDAB0MHzGBjxPsAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABoAAAAYCAYAAADkgu3FAAACGUlEQVR4AeyUSUhWURTHnxVUu6BaVNBARAWtooGIBmpRUEGLWlXrqIgWQdGiCWpTUDTRpnTjStypG0GccEBBEEQUBRFEBIeFAyoo+vs9vnt5im6Ez4X48f/dc+55791zzx2+Lck6/TYTrXmhN8TSPaf8b5AqnxW9JsM+SJWvRCcY/QDUQqqVEh3hyR04BSs930b8PFyGrZDVbjrH4C6oARr7BcsH+syD37AXnsIXyOo0nVZwIBOV4ffCVVAvaPz+FXYC3Kfv2O3ZRNcJPAEHKcQ6u5vYoJM41VACb+ATOOOj2GFQ72huwDSUg/5t7Ew20TkCu+AxHIR/8BCC/uNMQTxJ+DtgBDoh6DjOfoj7g59kE9UQmIdf0A+W3YVVTuICThXMQtAlHAdcwAZdyTnGc26yJFET0YvgknRgPRCPsMq4NvvxIQKHwQliotyvIXrdEBUq+kmkB1rgLZwF19kNxU0KbKABgq7lnHrsPXAvMIkV1eFYpSe0CD9W5F74gTE5QzMJlaAabWAPKKv5gDMHVv8A2ww7wf1pw6qPNBUQE72k43l3f4rxv8ItGAPlIC6pB8Hj+oPgM3Ayzrgd30PhKvzFvw+ezlFsKcREvuzaOoB3wI33vvhOwCX1Cvwh4BXw+PoX856+1WFSef98rnViaTDskR1PnJdv0M4qjBP3HUyqGdo+WC7vlxXGeDZRDObD2Uy05lVdt6VbBAAA///MUIy2AAAABklEQVQDAKUBYjHLAOFxAAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAYCAYAAABTPxXiAAADnElEQVR4AeyWZ6iPURjAX3uPzEiyZ4nskZFkj6wo5IsRki/IKklmQkYUskIiJZIPZGSEbCLJVmRlZvv9/pz3vveibkrde7u353ee8Y7zPuc8z/nfvFEO+MtNIqtsYu5O5O7Ev6/AIB7dDrFkx3KaxNdXg1iyWxLF+fIWcBRiSSbRhmgnyANJKYGTvK8sfh8oD0ohhtbQC0rC36QyF3pCU8gPGcV5mxDsDIUhKaVwakM/8Nk7aP2C6Ch83CKcwbAWZkGQqhhPoDsoxRh2gB98Hm3Se9CtYCTcgAqQUcYR8LlK6P6wDZJSA+c4jIJGsB8uwHBQhjGshIXwBXyHfmohTcLtcQWtNbNsyE1BXLkiOJdAGcGwBXZBFTD5AeilMBv8SBPDjKUO1nJw4nVo5+iGzgdKRYZjcA1M1ncdwm4ML0BZxdAV7sFZ0JZH2KmdaICxAnyoOvogBPGD7uI8BKU0w15oDt/Bk+IDWjEB9SuHBKF8JhIzod3o3vAVlGUMruh0dBAXzusnQgBtPzRDp+sH/FQSGzFchSHoT2B5oCJrtAOG24xKyXxGP7Ij+iqYIColXRg/w0lIymmcN2CZ3kS70s6HGZm4C3EG5zkEaYdxEZwLlRJ7tgDWH5MgnhKb5gjWS1DqMVjfySQIRTaTL0y+zIQHctFd9IMxY7EJW+KZhAn5rKVLKLKXLCvn1Reb2ngyZtyFsx+Su2M8tRMaPlgXI3mDu0AoMgmb3hrUt4eKYiSTMGYp2rBluGbToaLJDB4Mj9FzoS3chregmLw6uXuedH6P85rMWG8Ak/AwCYu0gZg7Eydh/b0naN2hIj/Sk+IdjiVgqZ3DVtozfIPkSvlxxvYRHw+HQRnKcAXCxCZq/dsXhCPLyNUtpwMuwBK04unkqRQS9AQzCa+NZrgOlm+chM5Mgh6Ta9A7wWZ3gs3Y1meoWY/AU8SeQRBPFxP2tHIhQl9N4waP5dVoV85/F1yQW/iKB8YEDO9bjN4KM+AB+C5L9zK24gHgb8gmnFoQko2TIBbZcPUxvLkv2ob3+PPonIMfxEl7BOeXdpf8TZmHPxU8uVCRPWIPeL77HnvjgBcS+NvkqbOemEe612tim8wYdJAFGDa8CU/BDnOkS4J45Gr7g2V56X9ksIZRsbgDr2MvzfAkcQXTIj8tJ7O57+Nqo34TS9l5w3Urw3mDHx54imF/odLEH7s0L5taWTmJTC9pbhKZXqr/fGOO2IkfAAAA//9um27rAAAABklEQVQDADY1tjGiw+JsAAAAAElFTkSuQmCC>

[image6]: <data:image/png;base64,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>

[image7]: <data:image/png;base64,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>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA0AAAAXCAYAAADQpsWBAAABT0lEQVR4AdSRvSuFYRiHX0QGiRGlZCAZ/AUSg0yUTcliMfgbbMpiMhktMthtPpIMNlEUMojRpJCP63ryvJ68x3vqbOf0u97767l77vs5jVkNvzpr6mTFPijV350WOL0OpUqbmji5CC1QKpuaOdEG/TAIp2BsDbcoC8OkZ2AJGqAVjG3ELcqmdtIdMAVP8AjG1nCLsnBIehPc5Ri78cMzNqoLpweCbNJxn16cfaikCZJDEBSbxojc5wBbSXckbyEoNo0T3cMNqHk+/gW+7CS+jxNrWWwaoXAG7+CtA9gvmIZXWAF3xmR5k4/RTWYZRmELPsEGra/5QRwUb1olWoNz2IFrUEd8ZmEXCk0uuUfhBK4gylsccZvEHATFmwzc500nwb0c0T/+IubTpphL7QuBNzneJX5QtSbHc9wHTjsJ5vf1QvDPxxElL1e7KT+YOt8AAAD//8oAlzIAAAAGSURBVAMAdlE3L66eTcQAAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,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>