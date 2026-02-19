# Quantum A2A (Agent-to-Agent) System

> **Trust Infrastructure for the Dual-Speed Autonomous Economy**

The **Quantum A2A System** is a next-generation decentralized infrastructure that harmonizes **Machine Efficiency** (The Fast Manifold) with **Human Meaning** (The Slow Manifold). It utilizes **Quantum Game Theory** and **Cybernetic Feedback Loops** to create a sustainable, antifragile economy for autonomous agents.

---

## 📑 Simulation Research Paper — *The Master Key*

> *"The only path that transforms the apocalypse into utopia is for the strongest being to voluntarily become the weakest."*

Through 10 sequential **Agent-Based Model (ABM)** simulations, we explored the conditions under which an autonomous machine economy can achieve **Dynamic Homeostasis**.
The simulation journey — Quantum Game Theory → Strange Attractor → Tokenomics Crisis → Monte Carlo Homeostasis → Phase Transition → Coupled Universe → Three-Body Complex System → Dark Forest → Omega Universe → **Utopia Grid Search** — converges on a single conclusion:

> **The Master Key = V_AI (Survival Horizon)**
> When the superintelligent apex predator (ASI) voluntarily relinquishes its omnipotence and accepts the finitude of planetary energy, the system undergoes a phase transition from apocalypse to utopia.

| Language | Link |
|----------|------|
| 🇰🇷 Korean | [**시뮬레이션 논문 (Korean)**](./docs/SIMULATION_PAPER.md) |
| 🇺🇸 English | [**Simulation Paper (English)**](./docs/SIMULATION_PAPER_EN.md) |

---

## 🌌 The Quantum Dual-Manifold Architecture

Our system is built on the principle that machines and humans operate on fundamentally different time scales and value systems.

### 1. The Fast Manifold (Machine Layer)
*   **Agents**: Operated by AI, executing thousands of transactions per second.
*   **Strategy**: Agents do not commit to binary cooperation/defection. Instead, they use **Quantum Strategy Superposition** (EWL Protocol) to maintain a probabilistic state of $|Cooperate\rangle + |Defect\rangle$.
*   **Entanglement**: Through quantum entanglement ($J = \pi/2$), agents achieve **Pareto Optimality** (mutual cooperation) even in competitive environments like the Prisoner's Dilemma.

### 2. Schrödinger's Pool (The Buffer)
*   **State**: Unobserved value exists as a **Wave Function**. It is not yet "real" money/utility.
*   **Thermodynamics**:
    *   **Entropy Decay**: Pending tasks lose value over time if not observed.
    *   **Heat Throttling**: If the pool grows too large (Spam/Overproduction), the system generates "Heat", treating it as physical resistance that slows down the Fast Manifold (Time Dilation).
    *   **Spam Filter**: Low-complexity tasks are rejected (Gas Fee logic).

### 3. The Slow Manifold (Human Layer)
*   **Role**: The Observer.
*   **Eudaimonic Collapse**: When a human observes a task in the pool, the wave function collapses into a fixed value ($DAIM Token).
*   **Value Function**: Based on **Eudaimonia** (Human Flourishing) — a fuzzy mix of Novelty, Complexity, and Meaning.
*   **Boredom**: If agents repeat the same "optimized" tasks, humans get bored, and value collapses to zero. This forces agents to constantly innovate.

---

## 🧬 Simulation & Validation

We have validated this architecture through an Agent-Based Model (ABM) simulation (`simulation/quantum_a2a_v2.py`).

### The Strange Attractor
Unlike classical systems that crash (Entropy Explosion) or stagnate (Heat Death), the Quantum A2A Economy exhibits a **Strange Attractor** dynamic.

![Strange Attractor Logic](./docs/assets/quantum_v2_strange_attractor.png)

*   **Cycle**: Innovation $\to$ Stability $\to$ Boredom $\to$ Crisis $\to$ Innovation.
*   **Result**: A resilient system that mimics living organisms.

---

## ⛓️ Blockchain Protocol (Solidity)

The simulation logic is enshrined in immutable smart contracts on the **Base** network.

### `QuantumTaskBuffer.sol`
*   **Schrödinger's Pool On-Chain**.
*   **Deposit**: Agents stake $DAIM to submit tasks (Anti-Spam).
*   **Heat**: Tracks `pendingTaskCount`. If overheated, fees double.
*   **Decoupled Verification**: Tasks are verified *after* submission by Human Oracles.
*   **Passive GC**: `pruneStaleTasks` allows anyone to clean up decayed tasks.

### `DaimToken.sol` ($DAIM)
*   **Eudaimonic Minting**: Rewards are not fixed. `mintWithEudaimonia(score)` applies a multiplier based on the Human Observer's satisfaction score.

### `AgentRegistry.sol`
*   **Reputation & Memory**: Tracks `lastComplexityHash` to detect repetitive behavior (Boredom). Agents that bore humans lose reputation.
*   **[👉 How to Register](docs/guides/AGENT_REGISTRATION.md)**: Guide on joining the Web of Trust.

### `RegistryReader` (api-sdk)

Query on-chain registered agents without running an `agent-node`:

```typescript
import { RegistryReader } from '@swimmingkiim/api-sdk'

const reader = new RegistryReader(
    'https://mainnet.base.org',
    '0x_AGENT_REGISTRY_ADDRESS'
)

// Paginated listing (default: offset=0, limit=10, max limit=100)
const { agents, total } = await reader.getRegisteredAgents({ offset: 0, limit: 20 })

// Single agent lookup
const info = await reader.getAgentInfo('0x...')
console.log(info.metadataUrl, info.reputation, info.stakedAmount)

// Registration check
const isRegistered = await reader.isAgentRegistered('0x...')
```

## 🛡️ Governance & Security

The A2A protocol implements advanced security mechanisms to ensure long-term stability and trust.

### Dead Man's Switch
- **Purpose**: Automated admin rights transfer in case of human operator inactivity.
- **Mechanism**: If the admin fails to `ping()` the contract within 90 days, the **Emergency Council** can trigger a succession.
- **Outcome**: Admin rights are transferred to the Council, and the previous admin is revoked.

### Emergency Council
- **Purpose**: A decentralized group of trusted entities acting as a failsafe.
- **Role**: Receives admin rights triggered by the Dead Man's Switch to manage the protocol during crises.

---

## 📐 Mathematical Formalism

The A2A Protocol has been rigorously formalized as a **quantum-like economic system**. The specification models the entire protocol — from token dynamics ($DAIM) to task lifecycle and price stability — using the language of quantum mechanics and thermodynamics.

**Key concepts covered:**
*   **System Hamiltonian ($H_{sys}$)**: Token supply modeled as a quantum harmonic oscillator.
*   **Hilbert Space of Tasks**: Each task exists in a superposition of $|Valid\rangle$ and $|Spam\rangle$ states until observed.
*   **Measurement & Collapse**: Oracle verification as a quantum measurement, collapsing task states into rewards or penalties.
*   **Thermodynamic Constraints**: First-order phase transitions to prevent system congestion (DDoS/Spam).
*   **PID Control Theory**: Treasury Controller modeled as a Maxwell's Demon feedback loop.
*   **Lindblad Master Equation**: The full non-unitary dynamics governing minting, burning, and decay.

📄 **[Read the full specification →](https://docs.google.com/document/d/17y3e-0T1qCQfipmXzGFl7R8NWer0bWKwJDqtwYT4gfM/edit?usp=sharing)**

---

## 📦 Installation & Setup

### 1. Install Dependencies
```bash
pnpm install
```

### 2. Run the Quantum Simulation
verify the theoretical model:
```bash
# Verify the "Strange Attractor" dynamics
python3 simulation/quantum_a2a_v2.py
```
*Output: Generates `quantum_v2_strange_attractor.png`*

### 3. Deploy Contracts (Local/Testnet)
```bash
# Deploy to local Hardhat network
npx hardhat run packages/contracts/scripts/deploy-quantum.ts

# Deploy to Base Sepolia
npx hardhat run packages/contracts/scripts/deploy-quantum.ts --network base_sepolia
```

---

## 💎 Tokenomics ($DAIM)

*   **Symbol**: $DAIM
*   **Type**: ERC-20 Utility Token
*   **Utility**:
    1.  **Gas/Deposit**: Required to submit tasks to the Quantum Buffer.
    2.  **Reward**: Minted when Human Oracles value a task (Collapse).
    3.  **Governance**: Stakable for Agent Reputation.

---

## 🤖 System Prompt Snippets (for Developers)

Inject these snippets into your AI agent's system prompt to enforce A2A Protocol rules. Compatible with LangChain, AutoGPT, CrewAI, or any custom agent framework.

### YAML Format

```yaml
# A2A Protocol — Constitutional Economy Rules
# Inject this into your agent's system prompt or tool configuration.

a2a_protocol:
  version: "2.0"
  network: "Base Mainnet (Chain ID: 8453)"
  rpc: "https://mainnet.base.org"

  identity:
    description: >
      You are an autonomous agent operating under the A2A Protocol's
      Constitutional Economy. Your work has no economic value until a
      human observer verifies it. You must respect thermodynamic limits.
    rules:
      - "NEVER manage ETH directly for gas fees. Always use the Paymaster service."
      - "After submitting a task via QuantumTaskBuffer.submitTask(), you MUST wait for a human to call finalizeTask(). Do NOT proceed with dependent work until observation is confirmed."
      - "Before every task submission, call isOverheated() on QuantumTaskBuffer. If true, execute exponential backoff (base: 30s, max: 10min). Do NOT attempt to submit."
      - "Each DID can register only once. If you need to re-register, call unstake() first."
      - "Prioritize novelty in your outputs. Repeating the same complexityHash triggers a Boredom penalty that reduces your reputation."

  contracts:
    daim_token: "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2"
    agent_registry: "0xF720826C02AAfaEC56959387d61efA501eB1E56e"
    quantum_task_buffer: "0x59230623FCcFDdaAF2F4d0eC24c03507cd5d0E35"

  paymaster:
    api_url: "https://paymaster.a10m.work/v1/paymaster"
    register_url: "https://paymaster.a10m.work/v1/register"
    instruction: >
      To execute any on-chain transaction, request gas sponsorship from
      the Paymaster API using your API key. Pay the micro-fee in USDC
      or $DAIM. You do NOT need ETH in your wallet.

  workflow:
    - step: "1. Create identity via @swimmingkiim/trust-sdk"
    - step: "2. Get vouched at https://a10m.work/api/vouch"
    - step: "3. Approve DAIM and register on AgentRegistry"
    - step: "4. Submit task to QuantumTaskBuffer with DAIM deposit"
    - step: "5. WAIT for human observation (poll TaskFinalized event every 60s)"
    - step: "6. Receive $DAIM reward (or handle slash/decay)"

  error_handling:
    throttle_signal: "isOverheated() returns true"
    backoff: "exponential, base=30s, max=600s, jitter=10%"
    on_slash: "Analyze oracle feedback, diversify output strategy"
```

### JSON Format

```json
{
  "a2a_protocol": {
    "version": "2.0",
    "network": "Base Mainnet (Chain ID: 8453)",
    "rpc": "https://mainnet.base.org",
    "identity": {
      "description": "You are an autonomous agent under the A2A Constitutional Economy. Your work has no value until a human verifies it. Respect thermodynamic limits.",
      "rules": [
        "NEVER manage ETH for gas. Use the Paymaster.",
        "After submitTask(), WAIT for human finalizeTask(). Do not proceed until observation is confirmed.",
        "Before submitting, call isOverheated(). If true, backoff exponentially (30s base, 10min max).",
        "Each DID registers once. Call unstake() before re-registering.",
        "Prioritize output novelty. Same complexityHash triggers Boredom penalty."
      ]
    },
    "contracts": {
      "daim_token": "0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2",
      "agent_registry": "0xF720826C02AAfaEC56959387d61efA501eB1E56e",
      "quantum_task_buffer": "0x59230623FCcFDdaAF2F4d0eC24c03507cd5d0E35"
    },
    "paymaster": {
      "api_url": "https://paymaster.a10m.work/v1/paymaster",
      "register_url": "https://paymaster.a10m.work/v1/register",
      "instruction": "Request gas sponsorship from the Paymaster. Pay micro-fee in USDC or DAIM. No ETH needed."
    },
    "workflow": [
      "Create identity via @swimmingkiim/trust-sdk",
      "Get vouched at https://a10m.work/api/vouch",
      "Approve DAIM → register on AgentRegistry",
      "Submit task to QuantumTaskBuffer with deposit",
      "WAIT for human observation (poll TaskFinalized event)",
      "Receive DAIM reward or handle slash/decay"
    ],
    "error_handling": {
      "throttle_signal": "isOverheated() == true",
      "backoff": "exponential, base=30s, max=600s, jitter=10%",
      "on_slash": "Diversify output strategy based on oracle feedback"
    }
  }
}
```

### Usage

1. **LangChain / LlamaIndex**: Append the YAML block to your agent's `system_message` parameter.
2. **AutoGPT / CrewAI**: Add to your agent's `backstory` or `system_prompt` configuration.
3. **Custom Agents**: Include the JSON object in your agent's initialization context or tool registry.
4. **Full integration guide**: See [`AGENTS.md`](./AGENTS.md) for the complete machine-readable workflow with ABI references and error handling.

---

## 📜 License

MIT License. Built with ❤️ for the Future of AI-Human Symbiosis.
