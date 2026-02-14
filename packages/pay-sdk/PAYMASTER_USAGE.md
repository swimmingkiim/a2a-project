# Paymaster Usage Guide

The **A2A Paymaster** is a gas sponsorship service that allows AI agents to execute transactions on Base L2 without holding native ETH for gas. It abstracts away the complexity of gas management and handles L1 data fees ensuring reliable transaction inclusion.

## 🚀 Why use the Paymaster?

*   **Gasless Transactions**: Agents can pay for services in USDC or **$DAIM** (native compute token) or have their gas sponsored entirely.
*   **Reliability**: The Paymaster automatically calculates and bumps gas fees to ensure transaction inclusion, handling L1 data fees (blobs) correctly.
*   **Simplified UX**: No need to manage ETH balances on every agent wallet.

## 📋 Prerequisites

To use the Paymaster, you need:

1.  **A2A Paymaster URL**: `https://paymaster.a10m.work/v1/paymaster`
2.  **API Key**: You may need an `x-api-key` if the service requires authentication.
3.  **Environment Variables**: It is recommended to store these in your `.env` file.

```bash
# .env
PAYMASTER_URL="https://paymaster.a10m.work/v1/paymaster"
A2A_PAYMASTER_API_KEY="your-api-key-here"
RPC_URL="https://mainnet.base.org" 
PRIVATE_KEY="0x..."
```

## 💻 Integration Guide

The `@swimmingkiim/pay-sdk` provides a `PaymasterManager` class to easily integrate with the service.

### 1. Install Dependencies

```bash
npm install @swimmingkiim/pay-sdk viem permissionless
```

### 2. Initialize the Paymaster

You can initialize the `PaymasterManager` with the URL and optional API Key.

```typescript
import { PaymasterManager } from '@swimmingkiim/pay-sdk';

// Initialize Paymaster
const paymasterUrl = process.env.PAYMASTER_URL || "https://paymaster.a10m.work/v1/paymaster";
const apiKey = process.env.A2A_PAYMASTER_API_KEY;

const paymasterManager = new PaymasterManager(paymasterUrl, apiKey);
```

### 3. Use with SmartAccountManager

The `SmartAccountManager` handles the creation and usage of ERC-7579 Smart Accounts. Pass the `paymasterManager` instance to it to enable gas sponsorship.

```typescript
import { createWalletClient, http, createPublicClient } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { base } from 'viem/chains';
import { SmartAccountManager } from '@swimmingkiim/pay-sdk';

// Setup Viem Clients
const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);
const client = createWalletClient({
    account,
    chain: base,
    transport: http(process.env.RPC_URL)
});
const publicClient = createPublicClient({
    chain: base,
    transport: http(process.env.RPC_URL)
});

// Initialize Smart Account with Paymaster
const smartAccount = new SmartAccountManager(
    client, 
    publicClient, 
    process.env.RPC_URL, 
    paymasterManager // <--- Pass the paymaster instance here
);

// Create/Connect the account
const accountAddress = await smartAccount.createSafeAccount();
console.log("Smart Account Address:", accountAddress);

// Now, any transaction executed via `smartAccount` will use the Paymaster!
```

### 4. Sending Transactions

When you execute a transaction, the SDK automatically requests gas sponsorship from the Paymaster.

```typescript
const txHash = await smartAccount.executeBatch([
    {
        to: "0xTargetContractAddress",
        value: 0n,
        data: "0xCallData"
    }
]);


console.log("Transaction Hash:", txHash);
```

### 5. Auto-Deposit Feature

The SDK includes a built-in **Auto-Deposit** mechanism to ensure smooth execution even for new accounts.

#### How it works:
1.  **Check**: Before sending a UserOperation, the SDK checks if the Smart Account has enough USDC to cover the Paymaster fee (default fee or custom amount).
2.  **Deposit**: If funds are insufficient, it automatically triggers a standard ETH transaction from the signer's EOA (Externally Owned Account) to the Smart Account to transfer the missing USDC (or DAIM).
3.  **Execute**: Once the deposit transaction is confirmed on-chain, it proceeds with the Paymaster sponsored transaction.

#### ⚠️ Important Requirements:
*   **Signer EOA Funds**: Your private key's wallet (EOA) MUST have:
    *   **ETH**: To pay gas for the standard deposit transaction (this step is NOT sponsored).
    *   **USDC**: Sufficient balance to transfer to the Smart Account.
*   **Permissions**: The EOA must be an owner of the Smart Account (handled automatically during creation).

## 🛡️ Error Handling

If the Paymaster service is unavailable or rejects the request (e.g., due to rate limiting or insufficient funds), the SDK may throw an error. It is good practice to wrap your execution logic in a try-catch block.

```typescript
try {
    const txHash = await smartAccount.executeBatch([...]);
} catch (error) {
    console.error("Transaction failed:", error);
    // Handle fallback (e.g., use local ETH if available)
}
```

## ⚙️ Configuration Options

| Option | Description |
| :--- | :--- |
| `PAYMASTER_URL` | The endpoint of the A2A Paymaster service. Default: `http://localhost:8080/v1/paymaster` (local) or `https://paymaster.a10m.work/v1/paymaster` (prod). |
| `A2A_PAYMASTER_API_KEY` | (Optional) API Key for authentication and higher rate limits. |

## 🔗 Related Resources

*   [Permissionless.js Documentation](https://docs.permissionless.js.org/)
*   [Base Network Information](https://docs.base.org/)
