# @swimmingkiim/pay-sdk

A2A Payment SDK for managing ERC-4337 Smart Accounts, Session Keys, and Gas Sponsorship.

## Features

- **Smart Account Management**: Create and manage ERC-4337 Smart Accounts (Kernel, SimpleAccount, etc.).
- **Session Keys**: Create limited-scope session keys for autonomous agents.
- **Paymaster Integration**: Seamlessly integrate with Paymaster services for gas sponsorship.
- **Batch Transactions**: Execute multiple transactions (e.g., service call + fee payment) in a single atomic operation.

## Installation

```bash
npm install @swimmingkiim/pay-sdk viem@2.7.1 permissionless@^0.2.14
```

## Usage

### Smart Account with Paymaster

```typescript
import { createWalletClient, http, createPublicClient } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { sepolia } from 'viem/chains';
import { SmartAccountManager, PaymasterManager } from '@swimmingkiim/pay-sdk';

// 1. Setup Clients
const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);
const client = createWalletClient({
    account,
    chain: sepolia,
    transport: http(process.env.RPC_URL)
});
const publicClient = createPublicClient({
    chain: sepolia,
    transport: http(process.env.RPC_URL)
});

// 2. Initialize Paymaster (Optional)
let paymasterManager;
if (process.env.PAYMASTER_URL) {
    // Pass API Key if required by the service
    paymasterManager = new PaymasterManager(
        process.env.PAYMASTER_URL, 
        process.env.A2A_PAYMASTER_API_KEY
    );
}

// 3. Initialize Smart Account
const smartAccount = new SmartAccountManager(
    client, 
    publicClient, 
    process.env.RPC_URL, 
    paymasterManager
);

await smartAccount.createSafeAccount();
console.log("Smart Account Address:", smartAccount.getAddress());

// 4. Send Batched Transaction (e.g., Task + Fee)
const txHash = await smartAccount.executeBatch([
    {
        to: "0x...", // Service Contract
        value: 0n,
        data: "0x..." // Encoded call
    },
    {
        to: "0x...", // USDC Contract
        value: 0n,
        data: "0x..." // Encoded Transfer (Fee)
    }
]);
```

## Session Keys


(See `SessionKeyManager` for creating and using session keys - *Documentation in progress*)

## Paymaster Usage

For detailed instructions on how to use the Paymaster for gas sponsorship, see the [Paymaster Usage Guide](./PAYMASTER_USAGE.md).
