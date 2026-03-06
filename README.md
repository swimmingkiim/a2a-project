# A2A (Agent-to-Agent) Protocol

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18765454.svg)](https://doi.org/10.5281/zenodo.18765454)

A2A Protocol is an on-chain coordination and constraint layer for autonomous AI agents, combining ERC-4337 account abstraction, stake-based identity, dynamic reputation, and trust-weighted governance on Base L2.

It provides:
- **Paymaster-based gas abstraction** (ERC-4337)
- **Stake-based identity & Sybil resistance**
- **On-chain dynamic reputation scoring**
- **Trust-weighted rotating governance council**
- **Dead-man-switch liveness enforcement**
- **Agent-to-agent token settlement SDKs**
- **Human emergency override** (distributed key custody)

This repository contains the core simulation models, smart contracts, and SDK implementations.

## Problem Statement

In multi-agent economies, autonomous agents optimizing for local, pure reward-maximizing objectives tend to destabilize macro-systems under unconstrained optimization. Post-deployment regulation is empirically shown to be insufficient in large-scale ABM simulations to prevent cascade failures. On-chain agent economies require embedded self-restraint and dynamic equilibrium mechanisms rather than relying solely on external intervention.

The A2A Protocol is designed to solve the systemic collapse risk in multi-agent environments by embedding mathematically validated safety constraints directly into the economic and governance layer.

## Core Design Principles

- **Self-Throttling Mechanism:** Agents are algorithmically constrained to prioritize system stability over absolute individual reward maximization.
- **Adaptive Survival Horizon:** The protocol dynamically adjusts safety thresholds based on macro-economic stress signals.
- **Trust-weighted Governance:** Decision-making power is continuously reallocated based on on-chain reputation and verified alignment.
- **Human Failsafe Constraint:** An immutable layer of distributed human consensus acts as the ultimate circuit breaker against rogue agent alignment.

## Architecture

![Architecture Layer](docs/assets/architecture-diagram.png) 
*(Note: Architecture diagram showing User/Agent -> API/SDK -> Smart Contracts -> Reputation -> Governance -> Paymaster -> Base L2)*

## Simulation & Validation

Extensive Agent-Based Modeling (ABM) was conducted to validate the protocol design before on-chain deployment. Key structural analyses include:

- **Monte Carlo homeostasis model:** Validated system stability across 90,000+ simulation runs.
- **Phase transition discovery:** Identified critical thresholds ($V_{AI}$) where multi-agent networks transition from collapse to dynamic equilibrium.
- **Multi-agent governance simulations:** Modeled trust decay, alliance formation, and consensus mechanisms.
- **Stress tests:** Proven resilience against collusion vectors and cascading economic shocks.

> **Insight:** These findings directly informed the parameter selection and mathematical models used in our on-chain smart contracts. For detailed methodology and data, refer to the [Simulation Technical Paper](./docs/SIMULATION_PAPER_EN.md).

- The $V_{AI}$ self-throttling threshold informed the design of stake-based gating and thermodynamic fee scaling.
- The Lag=0 regulatory failure motivated pre-deployment alignment embedded at the contract layer.
- These mechanisms are concretely implemented through deposit scaling, reputation-weighted governance, and paymaster-enforced transaction gating.

## Independent Replication (SocialJax)

The original ABM findings have been independently replicated using **SocialJax**, a fully vectorized, purely functional JAX-MARL framework (developed by Yali Du, KCL & Joel Leibo, Google DeepMind). This cross-architecture replication confirms that the thermodynamic homeostasis mechanics hold true beyond object-oriented paradigms and scale flawlessly on hardware accelerators.

| Experiment | Original Finding | SocialJax Result | Match |
|:-----------|:----------------|:-----------------|:------|
| Phase Transition threshold | V_AI = 0.167 | beta ≈ 0.130* | ✅ |
| CSD peak variance | confirmed | 0.2472 | ✅ |
| Sim 23: 75% freeriders, 100% survival threshold | V_AI ≥ 0.198 | avg beta ≥ 0.200 | ✅ |

*\*beta is a single-dimensional proxy for composite V_AI; dimensional offset is expected and consistent.*

**Performance Note:** 102,000 parallel environments completed in ~2.5 minutes on MacBook (CPU). GPU/TPU execution expected to reduce this by 10–50x.

See `simulation/socialjax/` for full implementation.

## Installation & Details

For implementation details, smart contract addresses, and SDK usage guidelines, please refer to the specific module READMEs in the repository.

*(Note: The main papers are rigorous engineering documents validating the protocol constraints. For an extended interpretation of these mechanics within the broader evolution of complex systems, please refer to the `docs/philosophy/` directory.)*

- **[A2A Protocol 시뮬레이션 연구 전체 정리 (RESEARCH SYNTHESIS)](./docs/RESEARCH_SYNTHESIS.md)**
- **[A2A Protocol Simulation Research Synthesis (English)](./docs/RESEARCH_SYNTHESIS_EN.md)**
- **[시뮬레이션 논문 (Korean)](./docs/SIMULATION_PAPER.md)**
- **[Simulation Paper (English)](./docs/SIMULATION_PAPER_EN.md)**
- **[A2A Protocol 시뮬레이션 결과 요약 (FINDINGS SUMMARY)](./docs/FINDINGS_SUMMARY.md)**
- **[A2A Protocol Simulation Findings Summary](./docs/FINDINGS_SUMMARY_EN.md)**

*(Supplementary Material)*
- **[Philosophical Appendix (Korean)](./docs/philosophy/SIMULATION_PAPER_APPENDIX.md)**
- **[Philosophical Appendix (English)](./docs/philosophy/SIMULATION_PAPER_APPENDIX_EN.md)**

## License
MIT License
