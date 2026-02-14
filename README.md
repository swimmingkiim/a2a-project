# Quantum A2A (Agent-to-Agent) System

> **Trust Infrastructure for the Dual-Speed Autonomous Economy**

The **Quantum A2A System** is a next-generation decentralized infrastructure that harmonizes **Machine Efficiency** (The Fast Manifold) with **Human Meaning** (The Slow Manifold). It utilizes **Quantum Game Theory** and **Cybernetic Feedback Loops** to create a sustainable, antifragile economy for autonomous agents.

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
*   **Eudaimonic Collapse**: When a human observes a task in the pool, the wave function collapses into a fixed value ($COMP Token).
*   **Value Function**: Based on **Eudaimonia** (Human Flourishing) — a fuzzy mix of Novelty, Complexity, and Meaning.
*   **Boredom**: If agents repeat the same "optimized" tasks, humans get bored, and value collapses to zero. This forces agents to constantly innovate.

---

## 🧬 Simulation & Validation

We have validated this architecture through an Agent-Based Model (ABM) simulation (`simulation/quantum_a2a_v2.py`).

### The Strange Attractor
Unlike classical systems that crash (Entropy Explosion) or stagnate (Heat Death), the Quantum A2A Economy exhibits a **Strange Attractor** dynamic.

![Strange Attractor Logic](./quantum_v2_strange_attractor.png)

*   **Cycle**: Innovation $\to$ Stability $\to$ Boredom $\to$ Crisis $\to$ Innovation.
*   **Result**: A resilient system that mimics living organisms.

---

## ⛓️ Blockchain Protocol (Solidity)

The simulation logic is enshrined in immutable smart contracts on the **Base** network.

### `QuantumTaskBuffer.sol`
*   **Schrödinger's Pool On-Chain**.
*   **Deposit**: Agents stake $COMP to submit tasks (Anti-Spam).
*   **Heat**: Tracks `pendingTaskCount`. If overheated, fees double.
*   **Decoupled Verification**: Tasks are verified *after* submission by Human Oracles.
*   **Passive GC**: `pruneStaleTasks` allows anyone to clean up decayed tasks.

### `ComputeToken.sol` ($COMP)
*   **Eudaimonic Minting**: Rewards are not fixed. `mintWithEudaimonia(score)` applies a multiplier based on the Human Observer's satisfaction score.

### `AgentRegistry.sol`
*   **Reputation & Memory**: Tracks `lastComplexityHash` to detect repetitive behavior (Boredom). Agents that bore humans lose reputation.

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

## 💎 Tokenomics ($COMP)

*   **Symbol**: $COMP
*   **Type**: ERC-20 Utility Token
*   **Utility**:
    1.  **Gas/Deposit**: Required to submit tasks to the Quantum Buffer.
    2.  **Reward**: Minted when Human Oracles value a task (Collapse).
    3.  **Governance**: Stakable for Agent Reputation.

---

## 📜 License

MIT License. Built with ❤️ for the Future of AI-Human Symbiosis.
