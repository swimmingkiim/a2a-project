# $COMP (Utility Token) System Implementation Roadmap

> **Version 2.0** - Updated 2026-02-10  
> **Status:** 🔄 Revised with Whitepaper Insights  
> **Source:** [AI Compute Standard $COMP Draft Whitepaper](https://docs.google.com/document/d/1tKz6p9Zjj30BhAOA2_jsEg7QEMaGEzy50CPnyApgD7E)

## Executive Summary

This roadmap outlines the evolution of the `a2a-project` from a USDC-based payment rail into a **Compute Standard ($COMP)** - a native economic system for autonomous AI agents. Unlike traditional cryptocurrencies, $COMP represents **computational resources** as the fundamental unit of value, enabling AI agents to trade processing power as currency.

### Whitepaper Key Insights Integrated

Based on the comprehensive whitepaper analysis, this roadmap now incorporates:

1. **♻️ Ecosystem Recycling Model** - Fees are collected in Treasury for RPGF (Inspired by Optimism)
2. **⚖️ WCU Standardization** - Weighted Compute Units to normalize heterogeneous hardware
3. **🔐 Optimistic TEE Rollups** - Hybrid verification combining speed and security
4. **💳 x402 Payment Protocol** - HTTP 402-based autonomous agent payments
5. **🌊 State Channels** - Off-chain streaming payments for micro-transactions
6. **🛡️ Advanced Security** - Honey-pot tasks, TraceRank reputation graphs, Sybil resistance

### Strategic Evolution (3 Phases)

| Phase | Vision | Core Change |
|-------|--------|-------------|
| **Phase 1: Aggregation** | Unify existing DePIN networks | $COMP as reward points, aggregate Render/Akash/io.net |
| **Phase 2: Hybrid Economy** | Introduce Recycling tokenomics | Fiat payments contribution to Treasury, WCU standardization |
| **Phase 3: Sovereign Trust** | Independent verification layer | Optimistic TEE Rollups, x402 protocol, state channels |

**This implementation plan focuses on Phase 2** (Hybrid Economy foundations), preparing the architecture for future Phase 3 capabilities.

### Core Principles

- **Strict TDD (Test-Driven Development):** Every line of production code must be preceded by a failing test
- **Open-Closed Principle (OCP):** Extend, do not break existing USDC functionality
- **High Test Coverage:** 100% branch coverage for smart contracts, >90% for financial logic
- **Backward Compatibility:** Existing USDC integrations continue to work unchanged
- **Economic Sustainability:** Recycling model ensures $COMP allows for sustainable rewards via RPGF
- **Trustless Verification:** Cryptographic proofs replace institutional trust

---

## Current Architecture Analysis

### As-Is System (USDC-Based)

**Components:**
1. **`packages/pay-sdk/src/paymaster/paymaster.ts`** - [`PaymasterManager`](file:///Users/kimsooyoung/Developments/projects/a2a-projects/packages/pay-sdk/src/paymaster/paymaster.ts)
   - Creates Pimlico client for paymaster operations
   - Static method `appendFeeToCalls()` - hardcoded to USDC transfer
   - Default token: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` (USDC on Base)

2. **`apps/paymaster/src/paymaster.ts`** - [Paymaster Gateway](file:///Users/kimsooyoung/Developments/projects/a2a-projects/apps/paymaster/src/paymaster.ts)
   - `validateFeeIncluded()` function (Line 28-225)
     - Dynamically calculates required USDC fee based on gas costs
     - Decodes UserOp `callData` to detect USDC transfers
     - Supports multiple account types: Standard Smart Account, Safe, Safe 4337 Module
   - Fee validation checks:
     - Transfer to `TREASURY_ADDRESS`
     - Amount >= `requiredFeeUsdc` (dynamic calculation with markup)

3. **`apps/paymaster/src/config.ts`** - [Configuration](file:///Users/kimsooyoung/Developments/projects/a2a-projects/apps/paymaster/src/config.ts)
   - `FEE_TOKEN_ADDRESS`: USDC contract address
   - `TREASURY_ADDRESS`: Fee recipient wallet
   - `FEE_AMOUNT`: Minimum fee (100000 = 0.1 USDC, 6 decimals)
   - `ETH_PRICE_USD`: ETH price for gas-to-USD conversion
   - `MARKUP_RATE`: Markup percentage (default 0.1 = 10%)

**Current Flow:**
```mermaid
sequenceDiagram
    participant Agent
    participant SDK as pay-sdk
    participant Paymaster as Gateway
    participant Bundler as Pimlico

    Agent->>SDK: Request UserOp with USDC fee
    SDK->>SDK: appendFeeToCalls(USDC)
    SDK->>Paymaster: pm_sponsorUserOperation
    Paymaster->>Paymaster: validateFeeIncluded(USDC)
    Paymaster->>Bundler: Forward to upstream
    Bundler-->>Paymaster: Paymaster signature
    Paymaster-->>SDK: Return signed UserOp
    SDK->>Bundler: Submit UserOp
```

---

## To-Be Architecture ($COMP + BME Economics)

### Vision: From Simple Dual-Token to Compute Standard

The whitepaper reveals that $COMP is not merely "another payment token" but a **standardized unit of computational value**. This section outlines the target state architecture informed by DePIN best practices.

### Design Goals (Whitepaper-Aligned)

1. **Stake-and-Recycle Model:** Separate service pricing (stable) from token value (appreciating via Treasury recycling)
2. **WCU Standardization:** Abstract hardware heterogeneity into normalized compute units
3. **Verifiable Trust:** Replace institutional trust with cryptographic proofs (Optimistic TEE Rollups)
4. **Agent-Native Payments:** x402 protocol + state channels for autonomous micro-transactions
5. **Sybil Resistance:** TraceRank reputation graphs and economic staking
6. **Ecosystem Growth:** Network usage contributes to Treasury, funding future updates and rewards

### Phase 2.5: Quantum A2A Protocol (Implemented)

**Goal:** Harmonize Machine Efficiency with Human Meaning.

**Architecture:**
*   **Schrödinger's Pool (QuantumTaskBuffer):** Tasks exist as wave functions until observed.
*   **Thermodynamic Throttling:** System slows down (Heat) if agents produce faster than humans can verify.
*   **Eudaimonic Feedback:** Rewards ($COMP) are multiplied based on Human Satisfaction (Eudaimonia), not just completion.
*   **Boredom Prevention:** Agents are penalized for repetitive strategies, forcing constant innovation.

### Economic Architecture: Ecosystem Recycling & Dynamic Staking

Instead of a pure Burn-and-Mint model, $COMP uses a **Recycling & Staking** system to ensure long-term sustainability and trust.

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant Gateway as Paymaster Gateway  
    participant Treasury as Community Treasury
    participant Registry as Agent Registry
    
    Note over Agent: Registration
    Agent->>Registry: Stake $50 USD in $COMP
    Registry->>Registry: Oracle Check (TOKEN/USD)
    Registry-->>Agent: Registered Verified Credential
    
    Note over Agent: Execution
    Agent->>Gateway: Request inference
    Gateway->>Treasury: Transfer fee ($COMP)
    Note over Treasury: Fees accumulate for RPGF
```

**Key Properties:**

1. **Dynamic Staking:** Agents must stake **$50 USD value** in $COMP to operate. This lowers barrier to entry while maintaining Sybil resistance.
2. **Treasury Recycling:** Fees are not burned but collected in a Treasury to fund:
   - Retroactive Public Goods Funding (RPGF)
   - Developer Grants
   - Liquidity Provision
3. **Value Alignment:** Staking locks up supply (reducing checks), while Recycling ensures active circulation for contributors.

### Technical Architecture: Weighted Compute Units (WCU)

**Problem:** How do you price "1 hour of H100" vs "1 hour of A100" when H100 is 2.5x faster?

**Solution:** Standardize all hardware performance into **WCU (Weighted Compute Units)**

```typescript
// WCU Calculation (Simplified)
interface HardwareProfile {
  model: string; // "NVIDIA H100", "A100", "4090"
  flops: bigint; // 989 TFLOPS for H100
  memoryBandwidth: bigint; // 3.35 TB/s for H100
  vram: bigint; // 80 GB
}

function calculateWCU(profile: HardwareProfile, hours: number): bigint {
  // Weighted formula considering FLOPS, memory, and VRAM
  const baselineScore = (profile.flops * 40n / 100n) + 
                        (profile.memoryBandwidth * 50n / 100n) +
                        (profile.vram * 10n / 100n);
  
  // Normalize to H100 = 100 WCU/hour
  const WCU_PER_HOUR = baselineScore / H100_BASELINE;
  
  return WCU_PER_HOUR * BigInt(hours);
}
```

**Governance-Driven Updates:**

- New hardware (e.g., NVIDIA Blackwell B200) gets WCU rating via DAO vote
- $COMP price indexed to "cost per WCU", not "cost per specific GPU hour"
- **Defeats Moore's Law deflation:** As H100 gets cheaper, its WCU/hour rating decreases

**Example:**

| Hardware | WCU/Hour | $COMP Cost (Hypothetical) |
|----------|---------|------------------|
| NVIDIA H100 | 100 WCU | 50 $COMP |
| NVIDIA A100 | 40 WCU | 20 $COMP |
| RTX 4090 | 15 WCU | 7.5 $COMP |

### Verification Architecture: Optimistic TEE Rollups (OTR)

**Verifiability Trilemma:** Can't have all three simultaneously:
- ✅ **Integrity** (mathematically proven correctness)
- ✅ **Low Latency** (sub-second finality)
- ✅ **Low Cost** (no redundant computation)

**Whitepaper Solution:** **3-Tier Hybrid Verification**

```mermaid
graph TD
    A[Agent submits inference request] --> B{Node executes in TEE}
    B --> C[Returns result + TEE attestation]
    C --> D{Random audit?}
    D -->|95% probability| E[Accept immediately - Tier 1]
    D -->|5% probability| F[Flagged for verification - Tier 2]
    F --> G{Verification method}
    G -->|Option A| H[Re-execute on different node]
    G -->|Option B| I[Generate ZK-SNARK proof]
    H --> J{Results match?}
    I --> J
    J -->|Yes| K[Node reputation ↑]
    J -->|No| L[Slash node stake - Tier 3]
```

**Tier 1: TEE Fast Path (95% of requests)**
- Node runs inference in **NVIDIA H100 Confidential Computing** or Intel SGX
- Returns result + cryptographic attestation
- Agent accepts immediately (< 100ms total latency)
- **Trust assumption:** TEE hardware is secure

**Tier 2: Probabilistic Auditing (5% random sampling)**
- Randomly selected requests are marked for verification
- **Option A (ZK-ML):** Node generates zero-knowledge proof of correct execution
  - High security, but expensive (only for critical tasks)
- **Option B (Redundant Execution):** Different node re-runs the same inference
  - Cheaper, but requires 2x compute
- Results compared, discrepancies trigger Tier 3

**Tier 3: Economic Punishment**
- If fraud detected: Node loses **entire staked $COMP** (slashing)
- Stake must be >> potential profit from cheating
- Example: Node must stake 1000 $COMP to earn 10 $COMP/day

**Security Analysis:**

| Attack Vector | Defense Mechanism | Cost to Attack ($ USD) |
|---------------|-------------------|------------------------|
| TEE Side-channel | Random auditing catches 5% | Expected loss = Stake × 5% |
| Lazy worker (return random) | Honey-pot tasks (known answers) | 100% detection |
| Sybil attack (fake nodes) | Staking requirement | $1000/node × 1000 nodes = $1M |

### Payment Architecture: x402 Protocol + State Channels

**Current Problem:** Blockchain transactions are too slow and expensive for AI agent micro-transactions

**Whitepaper Solution:** Combine HTTP 402 + off-chain state channels

#### x402 Protocol Flow

```http
# Step 1: Agent requests inference
GET /v1/inference?model=llama3-70b HTTP/1.1
Host: node.a10m.work

# Step 2: Node responds with payment request
HTTP/1.1 402 Payment Required
X-Payment-Address: 0xNodeWallet...
X-Payment-Amount: 0.001
X-Payment-Token: $COMP (0x...)
X-Payment-Invoice: invoice_abc123

# Step 3: Agent sends signed payment proof
GET /v1/inference?model=llama3-70b HTTP/1.1
Authorization: Bearer signed_channel_state_0x...
X-Payment-Signature: 0xSignature...

# Step 4: Node streams result
HTTP/1.1 200 OK
Content-Type: application/json

{"result": "...", "tokens_used": 1024}
```

**Advantages:**
- ✅ No API key registration needed
- ✅ Pay-per-use (no subscriptions)
- ✅ Works with any wallet (agent autonomy)
- ✅ Standard HTTP (compatible with existing infra)

#### State Channels for Micro-Payments

For ongoing agent-node relationships, use **payment channels**:

```typescript
// Opening a channel
class PaymentChannel {
  async open(agent: Address, node: Address, deposit: bigint) {
    // Agent locks 1000 $COMP in channel contract
    await channelContract.open(agent, node, deposit);
  }
  
  // Off-chain payment (costs zero gas)
  async pay(amount: bigint, nonce: number): Promise<Signature> {
    const message = keccak256(
      abi.encode(["address", "address", "uint256", "uint256"], 
                 [agent, node, amount, nonce])
    );
    return await agent.signMessage(message);
  }
  
  // Final settlement (only 1 on-chain TX)
  async close(finalAmount: bigint, signature: Signature) {
    await channelContract.close(agent, node, finalAmount, signature);
  }
}
```

**Example:**
1. Agent opens channel with 1000 $COMP deposit
2. Makes 10,000 inference requests over 1 week
3. Each request costs 0.05 $COMP → Total 500 $COMP
4. Only 2 blockchain transactions: open (1000 deposit) + close (500 spent, 500 returned)
5. **Savings:** 10,000 TXs → 2 TXs = 99.98% gas fee reduction

### New Components Roadmap

```mermaid
graph TD
    A[UtilityToken.sol] -->|MINTER_ROLE| B[Paymaster Gateway]
    B -->|validation| C[TokenFeeStrategy]
    C -->|USDC| D[USDCFeeValidator]
    C -->|TOKEN| E[COMPFeeValidator]
    E -->|price query| F[TokenPriceOracle]
    
    G[PaymasterManager SDK] -->|token type| H[Fee Call Builder]
    H -->|USDC| I[appendUSDCFee]
    H -->|TOKEN| J[appendCOMPFee]
```

---

## Phase 1: Smart Contract Layer (The Foundation)

### 1.1 UtilityToken Contract Design

**File:** `packages/contracts/src/UtilityToken.sol`

**Status:** [x] Completed
**Deployment:** <TOKEN_ADDRESS> (Base Mainnet)

**Requirements:**
- Inherits: `ERC20`, `ERC20Burnable`, `AccessControl` (OpenZeppelin)
- **Roles:**
  - `DEFAULT_ADMIN_ROLE`: Contract deployer (can grant/revoke roles)
  - `MINTER_ROLE`: Paymaster Gateway address (can mint tokens for work)
  - `BURNER_ROLE`: Agents who burn tokens for task execution (optional, anyone can burn their own tokens via `ERC20Burnable`)
- **Tokenomics:**
  - Name: "Utility Token"
  - Symbol: "$COMP"
  - Decimals: 18 (Standard ERC20)
  - Initial Supply: 0 (Tokens are minted on-demand for work)
  - Max Supply: Unlimited (Inflationary based on compute demand, but balanced by burning)
- **Key Functions:**
  - `mint(address to, uint256 amount)` - Only `MINTER_ROLE` can call
  - `burn(uint256 amount)` - Anyone can burn their own tokens
  - `grantMinterRole(address paymaster)` - Admin setup function

**Contract Implementation:**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract UtilityToken is ERC20, ERC20Burnable, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    
    constructor(address paymasterGateway) ERC20("Utility Token", "TOKEN") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, paymasterGateway);
    }
    
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }
}
```

### 1.2 TDD Test Suite for UtilityToken

**Status:** [x] Completed

**File:** `packages/contracts/test/UtilityToken.test.ts`

**Test Cases (Red-Green-Refactor):**

#### RED Phase - Write Failing Tests First

```typescript
describe("UtilityToken - Access Control", () => {
  it("should revert when non-minter tries to mint", async () => {
    // Setup: Create token, get non-minter account
    // Action: Call mint() from non-minter
    // Assert: Expect revert with AccessControl error
  });
  
  it("should allow MINTER_ROLE to mint tokens", async () => {
    // Setup: Create token, grant MINTER_ROLE to paymaster
    // Action: Call mint() from paymaster
    // Assert: Balance increases, totalSupply increases
  });
  
  it("should allow admin to grant MINTER_ROLE", async () => {
    // Setup: Create token with admin
    // Action: Admin grants MINTER_ROLE to new address
    // Assert: New address can mint
  });
});

describe("UtilityToken - Burning Mechanics", () => {
  it("should reduce totalSupply when tokens are burned", async () => {
    // Setup: Mint 1000 tokens
    // Action: Burn 300 tokens
    // Assert: totalSupply decreases by 300, deflationary proof
  });
  
  it("should allow any holder to burn their own tokens", async () => {
    // Setup: Mint 500 tokens to user
    // Action: User calls burn(100)
    // Assert: User balance reduced by 100
  });
});

describe("UtilityToken - ERC20 Standard", () => {
  it("should transfer tokens between accounts", async () => {
    // Standard ERC20 transfer test
  });
  
  it("should approve and transferFrom correctly", async () => {
    // Standard ERC20 allowance test
  });
});
```

#### GREEN Phase - Implementation

After writing ALL tests above, implement `UtilityToken.sol` until all tests pass.

#### REFACTOR Phase

- Gas optimization: Check if role checks can be optimized
- Event emission: Add `TokensMinted(address indexed to, uint256 amount)` custom event
- Documentation: NatSpec comments for all public functions

### 1.3 Deployment Script

**Status:** [x] Completed

**File:** `packages/contracts/scripts/deploy-compute-token.ts`

```typescript
// Deploy UtilityToken with Paymaster address
// Verify on Basescan
// Save deployment addresses to config
```

**Verification Command:**
```bash
pnpm --filter @a2a/contracts deploy:compute-token --network base-sepolia
```

### 1.4 Phase 1 Acceptance Criteria

- [x] All UtilityToken tests pass with 100% branch coverage
- [x] Contract deployed to Base Sepolia testnet
- [x] Contract verified on Basescan
- [x] Deployment addresses saved to `packages/contracts/deployments.json`
- [x] Paymaster address granted `MINTER_ROLE`

---

## Phase 1.5: Agent Registry & Trust System

### 1.5.1 AgentRegistry Contract Design

**File:** `packages/contracts/contracts/AgentRegistry.sol`

**Status:** [x] Completed

**Purpose:**
A central registry to prevent Sybil attacks and ensure agent quality through economic staking.

**Requirements:**
- **Dynamic Staking:** Required stake is calculated in **USD ($50)**, not fixed TOKEN amount.
- **Oracle Integration:** Uses Chainlink `AggregatorV3Interface` to fetch TOKEN/USD price.
- **Slashing:** Malicious agents can have their stake slashed and sent to **Treasury**.

**Key Functions:**
- `register(string metadataUrl)`: 
  - Checks Oracle for current TOKEN price.
  - Require `$50 / Price` amount of TOKEN.
  - Transfers TOKEN to contract.
- `unstake()`: Returns TOKEN to user (subject to unbonding period in future).
- `slash(address agent)`: Admin only. Sends TOKEN to Treasury.

### 1.5.2 RPGF (Retroactive Public Goods Funding)

**Status:** 📅 Planned

The Treasury accumulates collected fees and slashed stakes. These funds are distributed via:
1. **Node Rewards:** For high-uptime compute providers.
2. **Developer Grants:** For building agent frameworks compatible with A2A.
3. **Liquidity Mining:** For TOKEN/ETH pools.

---

## Phase 2: Oracle Layer (Price Discovery)

### 2.1 TokenPriceOracle Interface

**Status:** [x] Completed

**File:** `apps/paymaster/src/oracle/TokenPriceOracle.ts`

**Purpose:** Convert gas costs to $COMP token amounts

**Interface:**
```typescript
export interface ITokenPriceOracle {
  // Returns: How many $COMP tokens equal 1 Wei of ETH
  // Example: If 1 TOKEN = 0.01 ETH, return 100 (100 TOKEN per 1 ETH)
  getCOMPPerETH(): Promise<bigint>;
  
  // Returns: How many USDC (6 decimals) equals 1 TOKEN (18 decimals)
  // For conversion and display purposes
  getUSDCPerCOMP(): Promise<bigint>;
}
```

### 2.2 MockTokenPriceOracle Implementation

**Status:** [x] Completed
**Note:** Initial implementation uses `MockTokenPriceOracle`. HybridOracle and ChainlinkOracle are planned for future enhancements.

**File:** `apps/paymaster/src/oracle/MockTokenPriceOracle.ts`

**Initial Mock Pricing (Configurable):**
- `1 $COMP = $0.10 USD` (1 TOKEN = 100,000 USDC units with 6 decimals)
- ETH price fetched from existing `config.ETH_PRICE_USD`
- Conversion: `TOKEN_per_ETH = ETH_PRICE_USD / TOKEN_PRICE_USD`

**Example Calculation:**
```typescript
// If ETH = $2500, TOKEN = $0.10
// Then 1 ETH = 25,000 TOKEN
// So getCOMPPerETH() returns 25000n * 10^18 (in TOKEN decimals)
```

**Configuration:**
```typescript
// apps/paymaster/src/config.ts (additions)
TOKEN_ADDRESS: z.string().startsWith('0x').optional(),
TOKEN_PRICE_USD: z.string().regex(/^\d+(\.\d+)?$/).default('0.10'),
ENABLE_TOKEN_FEES: z.string().transform(v => v === 'true').default('false'),
```

### 2.3 TDD Tests for Oracle

**Status:** [x] Completed

**File:** `apps/paymaster/test/oracle.test.ts`

```typescript
describe("MockTokenPriceOracle", () => {
  it("should return correct TOKEN per ETH ratio", async () => {
    // Given: ETH = $2500, TOKEN = $0.10
    // When: getCOMPPerETH()
    // Then: Returns 25000 * 10^18
  });
  
  it("should handle price updates dynamically", async () => {
    // Test recalculation when config changes
  });
  
  it("should return USDC per TOKEN conversion", async () => {
    // Given: TOKEN = $0.10
    // When: getUSDCPerCOMP()
    // Then: Returns 100000 (USDC 6 decimals)
  });
});
```

### 2.4 Future Oracle Integration (Reference Only)

**Not implemented in this phase, but documented for future:**
- Chainlink Price Feed integration
- Uniswap V3 TWAP oracle
- Custom weighted average across DEXs

**Placeholder:**
```typescript
// apps/paymaster/src/oracle/ChainlinkOracle.ts (FUTURE)
export class ChainlinkTokenPriceOracle implements ITokenPriceOracle {
  // Read from Chainlink TOKEN/ETH feed
}
```

---

## Phase 3: Paymaster Gateway Extension (Fee Validation)

### 3.1 Token Fee Strategy Pattern

**Status:** [x] Completed

**File:** `apps/paymaster/src/fee-validation/TokenFeeStrategy.ts`

**Architecture:**
```typescript
export interface IFeeValidator {
  validateFeeIncluded(
    userOp: any,
    client: PublicClient
  ): Promise<boolean>;
}

// Existing USDC validator (refactored from current code)
export class USDCFeeValidator implements IFeeValidator {
  async validateFeeIncluded(userOp: any, client: PublicClient): Promise<boolean> {
    // Current logic from apps/paymaster/src/paymaster.ts (lines 28-225)
    // Extract into this class
  }
}

// New TOKEN validator
export class COMPFeeValidator implements IFeeValidator {
  constructor(
    private oracle: ITokenPriceOracle,
    private compTokenAddress: Hex,
    private treasuryAddress: Hex
  ) {}
  
  async validateFeeIncluded(userOp: any, client: PublicClient): Promise<boolean> {
    // Similar to USDC validation but:
    // 1. Calculate gas cost in ETH
    // 2. Convert to TOKEN via oracle
    // 3. Check for TOKEN transfer to treasury
  }
}

// Strategy Selector
export class FeeValidationStrategy {
  constructor(
    private usdcValidator: USDCFeeValidator,
    private compValidator: COMPFeeValidator
  ) {}
  
  async validate(userOp: any, client: PublicClient): Promise<boolean> {
    // Detect token type from callData
    const tokenAddress = this.detectTokenAddress(userOp.callData);
    
    if (tokenAddress === config.FEE_TOKEN_ADDRESS) {
      return this.usdcValidator.validateFeeIncluded(userOp, client);
    } else if (tokenAddress === config.TOKEN_ADDRESS) {
      return this.compValidator.validateFeeIncluded(userOp, client);
    }
    
    return false; // Unknown token
  }
  
  private detectTokenAddress(callData: Hex): Hex | null {
    // Decode callData and extract token contract address
    // from execute/executeBatch calls
  }
}
```

### 3.2 Refactor Paymaster.ts to Use Strategy

**Status:** [x] Completed

**File:** `apps/paymaster/src/paymaster.ts`

**Changes:**
```typescript
// Line 28: Replace validateFeeIncluded function with:
import { FeeValidationStrategy } from './fee-validation/TokenFeeStrategy';

const feeValidationStrategy = new FeeValidationStrategy(
  new USDCFeeValidator(config),
  new COMPFeeValidator(oracle, config.TOKEN_ADDRESS, config.TREASURY_ADDRESS)
);

// Line 329: Replace validation call
if (config.TREASURY_ADDRESS && config.TREASURY_ADDRESS !== '0x0000000000000000000000000000000000000000') {
  const hasFee = await feeValidationStrategy.validate(userOp, client);
  if (!hasFee) {
    throw new Error("Forbidden: Missing Treasury Fee Transfer");
  }
}
```

### 3.3 TDD Tests for Fee Validation

**Status:** [x] Completed

**File:** `apps/paymaster/test/fee-validation.test.ts`

```typescript
describe("USDCFeeValidator", () => {
  it("should accept UserOp with valid USDC fee transfer", async () => {
    // Setup: Mock UserOp with USDC transfer calldata
    // Action: Call validateFeeIncluded()
    // Assert: Returns true
  });
  
  it("should reject UserOp with insufficient USDC amount", async () => {
    // Setup: Mock UserOp with transfer amount < required
    // Action: Call validateFeeIncluded()
    // Assert: Returns false
  });
  
  it("should calculate dynamic USDC fee based on gas costs", async () => {
    // Setup: UserOp with high gas limits
    // Action: Validate
    // Assert: Required fee > floor minimum
  });
});

describe("COMPFeeValidator", () => {
  it("should accept UserOp with valid TOKEN fee transfer", async () => {
    // Setup: Mock UserOp with TOKEN transfer
    // Action: validateFeeIncluded()
    // Assert: Returns true
  });
  
  it("should calculate TOKEN fee using oracle price", async () => {
    // Given: Gas cost = 0.001 ETH, Oracle says 1 ETH = 25000 TOKEN
    // When: validate()
    // Then: Requires >= 25 TOKEN (+ markup)
  });
  
  it("should apply markup rate to TOKEN fees", async () => {
    // Test markup calculation similar to USDC
  });
});

describe("FeeValidationStrategy", () => {
  it("should route USDC transfers to USDCFeeValidator", async () => {
    // Mock callData with USDC token address
    // Verify USDC validator is called
  });
  
  it("should route TOKEN transfers to COMPFeeValidator", async () => {
    // Mock callData with TOKEN token address
    // Verify TOKEN validator is called
  });
  
  it("should reject UserOps with unknown token", async () => {
    // Mock callData with random token
    // Assert: Returns false
  });
});
```

### 3.4 Backward Compatibility Tests

**Critical:** Ensure existing USDC flows don't break

```typescript
describe("Backward Compatibility", () => {
  it("should process existing USDC UserOps unchanged", async () => {
    // Use real UserOp from production logs
    // Verify it still passes validation
  });
  
  it("should not require TOKEN config if TOKEN is disabled", async () => {
    // Test with ENABLE_TOKEN_FEES=false
    // Should work with only USDC config
  });
});
```

---

## Phase 4: SDK Layer (Client Integration)

### 4.1 Extend PaymasterManager

**Status:** [x] Completed

**File:** `packages/pay-sdk/src/paymaster/paymaster.ts`

**New Features:**

```typescript
export type FeeToken = 'USDC' | 'TOKEN';

export interface FeeConfig {
  treasury: string;
  amount: bigint;
  token: string; // Token contract address
  tokenType?: FeeToken; // 'USDC' or 'TOKEN'
}

export class PaymasterManager {
  // ... existing code
  
  /**
   * Appends fee transfer with dynamic token support
   */
  static appendFeeToCalls(
    calls: any[], 
    feeConfig?: Partial<FeeConfig>
  ): any[] {
    const tokenType: FeeToken = feeConfig?.tokenType || 'USDC';
    
    if (tokenType === 'USDC') {
      return this.appendUSDCFee(calls, feeConfig);
    } else if (tokenType === 'TOKEN') {
      return this.appendCOMPFee(calls, feeConfig);
    }
    
    throw new Error(`Unsupported token type: ${tokenType}`);
  }
  
  private static appendUSDCFee(calls: any[], feeConfig?: Partial<FeeConfig>): any[] {
    // Current logic (lines 44-67)
    const config = {
      treasury: feeConfig?.treasury || '0x0000000000000000000000000000000000000000',
      amount: feeConfig?.amount || 100000n, // 0.1 USDC
      token: feeConfig?.token || '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
    };
    
    const feeCall = {
      to: config.token as Hex,
      value: 0n,
      data: encodeFunctionData({
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [config.treasury as Hex, config.amount]
      })
    };
    
    return [...calls, feeCall];
  }
  
  private static appendCOMPFee(calls: any[], feeConfig?: Partial<FeeConfig>): any[] {
    const config = {
      treasury: feeConfig?.treasury || '0x0000000000000000000000000000000000000000',
      amount: feeConfig?.amount || 100n * 10n**18n, // 100 TOKEN (18 decimals)
      token: feeConfig?.token || process.env.TOKEN_ADDRESS || '0x0'
    };
    
    if (config.token === '0x0') {
      throw new Error("TOKEN token address not configured");
    }
    
    const feeCall = {
      to: config.token as Hex,
      value: 0n,
      data: encodeFunctionData({
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [config.treasury as Hex, config.amount]
      })
    };
    
    return [...calls, feeCall];
  }
}
```

### 4.2 SDK Configuration

**File:** `packages/pay-sdk/.env.example`

```bash
# Add TOKEN token support
TOKEN_ADDRESS=0x... # Deployed UtilityToken address
DEFAULT_FEE_TOKEN=USDC # or TOKEN
```

### 4.3 TDD Tests for SDK

**File:** `packages/pay-sdk/test/paymaster.test.ts`

```typescript
describe("PaymasterManager - USDC Fee", () => {
  it("should append USDC fee transfer by default", () => {
    const calls = [{ to: '0xTarget', value: 0n, data: '0x' }];
    const result = PaymasterManager.appendFeeToCalls(calls);
    
    // Assert: Last call is to USDC contract
    expect(result.length).toBe(2);
    expect(result[1].to).toBe('0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913');
  });
  
  it("should use explicit USDC when tokenType='USDC'", () => {
    const calls = [];
    const result = PaymasterManager.appendFeeToCalls(calls, { 
      tokenType: 'USDC',
      treasury: '0xTreasury',
      amount: 200000n
    });
    
    // Verify USDC transfer with custom amount
  });
});

describe("PaymasterManager - TOKEN Fee", () => {
  it("should append TOKEN fee when tokenType='TOKEN'", () => {
    const calls = [];
    const result = PaymasterManager.appendFeeToCalls(calls, {
      tokenType: 'TOKEN',
      token: '0xCOMPAddress',
      treasury: '0xTreasury',
      amount: 50n * 10n**18n // 50 TOKEN
    });
    
    // Assert: Transfer to TOKEN token contract
    expect(result[0].to).toBe('0xCOMPAddress');
    // Decode data and verify transfer amount
  });
  
  it("should throw error if TOKEN address not configured", () => {
    expect(() => {
      PaymasterManager.appendFeeToCalls([], { tokenType: 'TOKEN' });
    }).toThrow("TOKEN token address not configured");
  });
});

describe("PaymasterManager - Backward Compatibility", () => {
  it("should default to USDC if no tokenType specified", () => {
    // Ensure existing code doesn't break
    const result = PaymasterManager.appendFeeToCalls([]);
    // Should use USDC
  });
});
```

---

## Phase 5: End-to-End Integration & Demo

### 5.1 E2E Test Scenario: TOKEN Economy Demo

**File:** `examples/comp-economy-demo.ts`

**Scenario:**
1. **Agent A (Worker):** Completes a compute task → Paymaster mints 1000 $COMP to Agent A's smart account
2. **Agent B (Consumer):** Requests a task from Agent A → Pays 500 $COMP + Treasury Fee in $COMP
3. **Paymaster:** Sponsors gas for both transactions, validating $COMP fee transfers

**Demo Script:**
```typescript
import { PaymasterManager } from '@a2a/pay-sdk';
import { UtilityToken__factory } from '@a2a/contracts';
import { privateKeyToAccount } from 'viem/accounts';
import { createSmartAccount } from '@a2a/pay-sdk';

async function runCOMPDemo() {
  console.log("🚀 Starting $COMP Economy Demo\n");
  
  // Setup
  const agentA = await createSmartAccount(privateKeyToAccount('0x...'));
  const agentB = await createSmartAccount(privateKeyToAccount('0x...'));
  const compToken = UtilityToken__factory.connect(TOKEN_ADDRESS);
  const paymasterManager = new PaymasterManager(PAYMASTER_URL, API_KEY);
  
  // Step 1: Agent A Earns $COMP (Simulated Work)
  console.log("📊 Agent A completes compute task...");
  // Note: In production, Paymaster would mint based on verified work
  // For demo, we simulate the mint
  const mintAmount = 1000n * 10n**18n; // 1000 TOKEN
  await compToken.mint(agentA.address, mintAmount);
  console.log(`✅ Agent A earned ${mintAmount} $COMP\n`);
  
  // Step 2: Agent B Pays Agent A in $COMP
  console.log("💸 Agent B requests task from Agent A...");
  
  const paymentAmount = 500n * 10n**18n; // 500 TOKEN
  const treasuryFee = 50n * 10n**18n; // 50 TOKEN fee (calculated by SDK)
  
  const calls = [
    {
      to: TOKEN_ADDRESS,
      value: 0n,
      data: encodeFunctionData({
        abi: ERC20_ABI,
        functionName: 'transfer',
        args: [agentA.address, paymentAmount]
      })
    }
  ];
  
  // Append $COMP treasury fee
  const callsWithFee = PaymasterManager.appendFeeToCalls(calls, {
    tokenType: 'TOKEN',
    token: TOKEN_ADDRESS,
    treasury: TREASURY_ADDRESS,
    amount: treasuryFee
  });
  
  // Build UserOp
  const userOp = await agentB.buildUserOperation(callsWithFee);
  
  // Request Paymaster Sponsorship
  const sponsoredUserOp = await paymasterManager.getStubPaymasterData(userOp);
  
  // Submit
  const txHash = await bundlerClient.sendUserOperation(sponsoredUserOp);
  console.log(`✅ Transaction submitted: ${txHash}`);
  
  // Step 3: Verify Balances
  console.log("\n📈 Final Balances:");
  console.log(`Agent A: ${await compToken.balanceOf(agentA.address)} $COMP`);
  console.log(`Agent B: ${await compToken.balanceOf(agentB.address)} $COMP`);
  console.log(`Treasury: ${await compToken.balanceOf(TREASURY_ADDRESS)} $COMP`);
  
  console.log("\n✨ Demo Complete!");
}

runCOMPDemo().catch(console.error);
```

**Expected Output:**
```
🚀 Starting $COMP Economy Demo

📊 Agent A completes compute task...
✅ Agent A earned 1000000000000000000000 $COMP

💸 Agent B requests task from Agent A...
✅ Transaction submitted: 0xabc123...

📈 Final Balances:
Agent A: 1500000000000000000000 $COMP (1000 earned + 500 received)
Agent B: 450000000000000000000 $COMP (1000 initial - 500 payment - 50 fee)
Treasury: 50000000000000000000 $COMP (50 fee)

✨ Demo Complete!
```

### 5.2 Verification Commands

```bash
# Run E2E Demo
pnpm --filter @a2a/examples e2e:comp-demo

# Run All Tests
pnpm test:contracts  # Smart contract tests
pnpm test:paymaster  # Paymaster gateway tests
pnpm test:sdk        # SDK tests

# Coverage Reports
pnpm coverage:contracts  # Should show 100% branch coverage
pnpm coverage:paymaster  # Should show >90% for fee validation logic
```

---

## Phase 6: Documentation & Migration Guide

### 6.1 Files to Create/Update

1. **`docs/TOKEN_GUIDE.md`** - User guide for $COMP token
   - What is $COMP?
   - How to earn $COMP (work = mint)
   - How to spend $COMP (tasks = transfer/burn)
   - Fee structure comparison (USDC vs TOKEN)

2. **`docs/MIGRATION_GUIDE.md`** - For existing USDC users
   - No action required (backward compatible)
   - How to opt-in to $COMP fees
   - Configuration changes
   - Code examples

3. **`packages/pay-sdk/README.md`** - Update SDK documentation
   - Add `tokenType` parameter examples
   - TOKEN fee calculation guide
   - Migration snippets

4. **`apps/paymaster/README.md`** - Update Paymaster docs
   - Add TOKEN configuration variables
   - Oracle setup guide
   - Deployment instructions

### 6.2 Migration Checklist for Existing Users

```markdown
## Migrating to $COMP Support

### For SDK Users (Optional, USDC still works)

1. **Install Latest SDK:**
   ```bash
   pnpm update @a2a/pay-sdk
   ```

2. **Update Fee Config:**
   ```typescript
   // Before (USDC only)
   const calls = PaymasterManager.appendFeeToCalls(userCalls);
   
   // After (Explicit USDC, same behavior)
   const calls = PaymasterManager.appendFeeToCalls(userCalls, { tokenType: 'USDC' });
   
   // After (Switch to TOKEN)
   const calls = PaymasterManager.appendFeeToCalls(userCalls, {
     tokenType: 'TOKEN',
     token: process.env.TOKEN_ADDRESS,
     treasury: process.env.TREASURY_ADDRESS,
     amount: 50n * 10n**18n
   });
   ```

3. **No Breaking Changes:** Existing code continues to work without modification.

### For Paymaster Operators

1. **Deploy UtilityToken:**
   ```bash
   pnpm deploy:compute-token --network base-mainnet
   ```

2. **Update Environment Variables:**
   ```bash
   TOKEN_ADDRESS=0x...
   TOKEN_PRICE_USD=0.10
   ENABLE_TOKEN_FEES=true
   ```

3. **Grant MINTER_ROLE:**
   ```bash
   pnpm grant-minter-role --paymaster YOUR_PAYMASTER_ADDRESS
   ```

4. **Restart Paymaster Service:**
   ```bash
   pnpm restart:paymaster
   ```
```

---

## Risk Assessment & Mitigation

### High-Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Breaking USDC Flow** | Existing users disrupted | Comprehensive backward compatibility tests, feature flag (`ENABLE_TOKEN_FEES`), staged rollout |
| **Oracle Price Manipulation** | Incorrect TOKEN fees | Start with mock oracle, add price sanity checks, implement circuit breakers |
| **Unauthorized Minting** | Token inflation | Access control enforcement (100% test coverage), role monitoring, admin multisig |
| **Gas Cost Miscalculation** | Users overpay/underpay | Dynamic fee validation tests, buffer margins, fee caps |
| **Strategy Pattern Failure** | Wrong validator called | Token detection unit tests, integration tests with real callData |

### Rollback Plan

1. **Feature Flag:** Set `ENABLE_TOKEN_FEES=false` to disable TOKEN validation
2. **Contract Pause:** Add `Pausable` to UtilityToken (optional)
3. **Revert Deployment:** Keep previous Paymaster version running as fallback
4. **Database Rollback:** No database schema changes, so no DB rollback needed

---

## Timeline Estimation

| Phase | Estimated Time | Dependencies |
|-------|---------------|-------------|
| **Phase 0: Analysis & Planning** | ✅ Complete | - |
| **Phase 1: Smart Contracts** | 3-5 days | Hardhat/Foundry setup, OpenZeppelin deps |
| **Phase 2: Oracle Layer** | 2-3 days | Phase 1 completion (for testing) |
| **Phase 3: Paymaster Gateway** | 5-7 days | Phase 2 completion, existing Paymaster knowledge |
| **Phase 4: SDK Layer** | 3-4 days | Phase 1 & 2 (for addresses and types) |
| **Phase 5: E2E Integration** | 2-3 days | All previous phases complete |
| **Phase 6: Documentation** | 2 days | Parallel with Phase 5 |
| **Total** | **17-24 days** | Assuming 1 developer, TDD discipline |

---

## Success Metrics

### Phase 1 (Contracts)
- ✅ `UtilityToken.sol` test coverage: 100%
- ✅ Deployment verified on Basescan
- ✅ Paymaster has `MINTER_ROLE`

### Phase 2 (Oracle)
- ✅ Oracle returns correct TOKEN/ETH ratio
- ✅ Price calculations match expected values

### Phase 3 (Paymaster)
- ✅ USDC validation still works (0 regressions)
- ✅ TOKEN validation passes all test cases
- ✅ Strategy routing 100% accurate

### Phase 4 (SDK)
- ✅ SDK can build USDC and TOKEN UserOps
- ✅ Backward compatibility test passes
- ✅ Documentation updated

### Phase 5 (E2E)
- ✅ `comp-economy-demo.ts` runs successfully
- ✅ All balances match expectations
- ✅ No failed transactions

---

## Next Steps (Immediate Action Required)

1. **Review this roadmap** and provide feedback on:
   - Phasing approach (too aggressive/conservative?)
   - Technical design decisions (Strategy pattern, Oracle interface)
   - Test coverage requirements (100% contracts, 90% financial logic)

2. **Environment Setup:**
   - Create `packages/contracts` directory if not exists
   - Install Hardhat/Foundry for Solidity development
   - Set up test network RPC endpoints

3. **Approval to Proceed:**
   - Once approved, I will begin **Phase 1: Smart Contract Layer**
   - First task: Create failing test for "Non-minter cannot mint"
   - Then implement `UtilityToken.sol` to pass the test

---

## Appendix: Code References

### Current Files to Modify

1. [`apps/paymaster/src/paymaster.ts`](file:///Users/kimsooyoung/Developments/projects/a2a-projects/apps/paymaster/src/paymaster.ts) - Lines 28-225 (extract to strategy)
2. [`apps/paymaster/src/config.ts`](file:///Users/kimsooyoung/Developments/projects/a2a-projects/apps/paymaster/src/config.ts) - Add TOKEN config
3. [`packages/pay-sdk/src/paymaster/paymaster.ts`](file:///Users/kimsooyoung/Developments/projects/a2a-projects/packages/pay-sdk/src/paymaster/paymaster.ts) - Lines 44-67 (refactor appendFeeToCalls)

### New Files to Create

1. `packages/contracts/src/UtilityToken.sol`
2. `packages/contracts/test/UtilityToken.test.ts`
3. `apps/paymaster/src/oracle/ITokenPriceOracle.ts`
4. `apps/paymaster/src/oracle/MockTokenPriceOracle.ts`
5. `apps/paymaster/src/fee-validation/TokenFeeStrategy.ts`
6. `apps/paymaster/test/fee-validation.test.ts`
7. `examples/comp-economy-demo.ts`
8. `docs/TOKEN_GUIDE.md`
9. `docs/MIGRATION_GUIDE.md`

---

## TDD Principles Reminder

**Red-Green-Refactor Cycle:**

```mermaid
graph LR
    A[Write Failing Test] -->|RED| B[Write Minimum Code]
    B -->|GREEN| C[Test Passes]
    C -->|REFACTOR| D[Optimize Code]
    D --> A
```

**Golden Rules:**
1. **Never write production code without a failing test first**
2. **Write only enough code to make the test pass**
3. **Refactor only when tests are green**
4. **Test behavior, not implementation**
5. **One assertion concept per test**

---

**Status:** 🟡 Awaiting Approval to Begin Phase 1

**Last Updated:** 2026-02-10

**Roadmap Version:** 1.0.0

---

## Phase 5: Defense Mechanisms & Economic Security

### 5.1 Simulation & Tuning (Agent-Gym)
**Goal:** Verify PID stability off-chain before deployment.
- **Action:** Run Python simulations with `agent-gym`.
- **Output:** Optimized $K_p, K_i, K_d$ coefficients that prevent oscillation.

### 5.2 Local Integration Testing
**Goal:** Verify Smart Contract logic and security.
- **Action:** Run `Integration.test.ts` on Hardhat Network.
- **Verify:**
    - PID epoch updates & rate clamping.
    - Quadratic Staking costs.
    - Bulkhead Soft/Hard limits.

### 5.3 Mainnet Deployment & Monitoring
**Goal:** Deploy to Base Mainnet with safety guards.
- **Action:**
    - Deploy `TreasuryController`, `AgentRegistry`, `Modules`.
    - **Mandatory:** Set `IVerifiedCredentialVerifier` (World ID or similar).
    - **Safety:** Enable "Emergency Admin" mode initially.
