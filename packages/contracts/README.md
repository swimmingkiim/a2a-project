# ComputeToken Smart Contract

Solidity smart contract for the A2A Project's $COMP token - a compute standard for AI agent economies.

## Overview

`ComputeToken` is an ERC-20 token representing computational resources in the A2A network. It implements:

- ✅ **ERC-20 Standard** - Full fungible token support
- 🔥 **ERC-20 Burnable** - Deflationary burn mechanism
- 🔐 **Access Control** - Role-based minting permissions
- 📊 **BME Economics** - Burn-and-Mint Equilibrium model

## Token Details

| Property | Value |
|----------|-------|
| **Name** | Configurable (e.g. "Compute Token") |
| **Symbol** | Configurable (e.g. "$COMP") |
| **Decimals** | 18 |
| **Initial Supply** | 0 (minted on-demand) |
| **Max Supply** | Unlimited (inflationary) |

## Roles

- **`DEFAULT_ADMIN_ROLE`**: Can grant/revoke roles (deployer)
- **`MINTER_ROLE`**: Can mint new tokens (Paymaster Gateway)

## Functions

### `mint(address to, uint256 amount)`
Mints new $COMP tokens to the specified address.
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

## Economic Model (BME)

The Burn-and-Mint Equilibrium model creates sustainable tokenomics:

1. **Demand (Burn)**: Network usage burns $COMP → Deflationary pressure
2. **Supply (Mint)**: Computational work mints $COMP → Inflationary rewards
3. **Equilibrium**: If `burn > mint` → Net deflation → Price appreciates

**Example Scenario:**
- 10,000 $COMP minted as node rewards
- 12,000 $COMP burned as usage fees
- **Result**: -2,000 supply (deflationary) → Value increases

## Security

- ✅ OpenZeppelin contracts (v5.0+)
- ✅ Role-based access control
- ✅ Zero address validation
- ✅ Comprehensive test coverage
- ✅ Hardhat verification support

## License

MIT
