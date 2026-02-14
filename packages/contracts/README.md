# DaimToken Smart Contract

Solidity smart contract for the A2A Project's $DAIM token - a compute standard for AI agent economies.

## Overview

`DaimToken` is an ERC-20 token representing computational resources in the A2A network. It implements:

- ✅ **ERC-20 Standard** - Full fungible token support
- 🔥 **ERC-20 Burnable** - Deflationary burn mechanism
- 🔐 **Access Control** - Role-based minting permissions
- 📊 **BME Economics** - Burn-and-Mint Equilibrium model

## Token Details

| Property | Value |
|----------|-------|
| **Name** | Configurable (e.g. "A2A Daim Token") |
| **Symbol** | Configurable (e.g. "$DAIM") |
| **Decimals** | 18 |
| **Initial Supply** | 0 (minted on-demand) |
| **Max Supply** | Unlimited (inflationary) |

## Deployed Addresses (Base Mainnet)

| Contract | Address |
|----------|---------|
| **DaimToken** | `0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2` |
| **AgentRegistry** | `0xF720826C02AAfaEC56959387d61efA501eB1E56e` |
| **QuantumTaskBuffer** | `0x59230623FCcFDdaAF2F4d0eC24c03507cd5d0E35` |
| **EmergencyCouncil** | `0x9347215D6eA62BF4bed324aC9c7E4Ffb7d33c07C` |
| **DeadMansSwitch** | `0x536DA557b820a37E54121476e3c883f3A16b97c7` |
| **Treasury** | `0x129154b7E3f0Ab0E59615ef578f6511b072FB431` |


## Roles

- **`DEFAULT_ADMIN_ROLE`**: Can grant/revoke roles (deployer)
- **`MINTER_ROLE`**: Can mint new tokens (Paymaster Gateway)

## Functions

### `mint(address to, uint256 amount)`
Mints new $DAIM tokens to the specified address.
- **Access**: `MINTER_ROLE` only
- **Use case**: Reward nodes for computational work

### `burn(uint256 amount)`
Burns tokens from caller's balance, reducing total supply.
- **Access**: Any token holder
- **Use case**: Protocol fees, deflationary mechanism (BME model)

### `burnFrom(address account, uint256 amount)`
Burns tokens from another account using allowance.
- **Access**: Any address with sufficient allowance

## Development

### Install Dependencies

```bash
pnpm install
```

### Compile Contract

```bash
pnpm compile
```

### Run Tests

```bash
pnpm test
```

**Test Coverage**: 100% (17/17 tests passing)

### Deploy to Testnet

```bash
# 1. Copy and configure environment variables
cp .env.example .env

# 2. Set PAYMASTER_ADDRESS and DEPLOYER_PRIVATE_KEY in .env

# 3. Deploy to Base Sepolia
pnpm deploy:sepolia
```

### Verify Contract

After deployment, verify on Basescan:

```bash
npx hardhat verify --network base-sepolia <CONTRACT_ADDRESS> <PAYMASTER_ADDRESS>
```

## Governance Contracts

### DeadMansSwitch (`contracts/governance/DeadMansSwitch.sol`)
- **Purpose**: Automated succession planning system.
- **Mechanism**: Requires active `ping()` from admin every 90 days. Failure transfers control to Emergency Council.

### EmergencyCouncil (`contracts/governance/EmergencyCouncil.sol`)
- **Purpose**: Decentralized crisis management.
- **Structure**: Multisig-like contract that receives admin rights upon Dead Man's Switch triggering.

## Economic Model (BME)

The Burn-and-Mint Equilibrium model creates sustainable tokenomics:

1. **Demand (Burn)**: Network usage burns $DAIM → Deflationary pressure
2. **Supply (Mint)**: Computational work mints $DAIM → Inflationary rewards
3. **Equilibrium**: If `burn > mint` → Net deflation → Price appreciates

**Example Scenario:**
- 10,000 $DAIM minted as node rewards
- 12,000 $DAIM burned as usage fees
- **Result**: -2,000 supply (deflationary) → Value increases

## Security

- ✅ OpenZeppelin contracts (v5.0+)
- ✅ Role-based access control
- ✅ Zero address validation
- ✅ Comprehensive test coverage
- ✅ Hardhat verification support

## License

MIT
