# A2A Paymaster Demo

This example demonstrates how to use the **A2A Paymaster** to sponsor transactions on Base Mainnet using the **Pay SDK**.

It showcases the **Auto-Deposit** feature, which ensures your Smart Account executes transactions seamlessly even if it starts with 0 USDC balance.

## 📋 Prerequisites

To run this demo successfully, you need:

1.  **Funded EOA (Signer Wallet)**:
    - The Private Key you use in `.env` must belong to a wallet that holds:
        - **ETH**: To pay for the ephemeral "Auto-Deposit" transaction (approx $0.05).
        - **USDC**: At least **0.6 USDC** on Base Mainnet.
    - *Note: You do NOT need to fund the Smart Account directly. The SDK handles this.*

2.  **API Key**: A valid `A2A_PAYMASTER_API_KEY`.

## 🛠️ Setup

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   ```
   - Set `PRIVATE_KEY` (Your funded EOA).
   - Set `A2A_PAYMASTER_API_KEY`.

## 🚀 Run

```bash
pnpm start
```

## 🔍 How it Works (The Flow)

1.  **Initialization**: Creates a **Safe Smart Account** (ERC-7579) controlled by your Private Key.
2.  **Balance Check**: The SDK checks if the Smart Account has enough USDC to pay the Paymaster fee (approx 0.6 USDC).
3.  **Auto-Deposit (If needed)**:
    - If the Smart Account balance is insufficient (e.g., 0 USDC), the SDK automatically triggers a standard transaction from your EOA to deposit the missing amount.
    - You will see a log: `[SmartAccount] 🔄 Auto-depositing...`
4.  **Sponsored Execution**:
    - Once funded, the SDK constructs the UserOperation.
    - It requests sponsorship from the A2A Paymaster.
    - It executes the transaction, paying the 0.6 USDC fee to the Treasury.
    - **Gas fees (ETH) are fully sponsored by the Paymaster.**

## 📊 Expected Output

```
Signer (EOA): 0x4e57...
Smart Account: 0xa9e4...

Preparing transaction with 0.6 USDC fee...
[SmartAccount] Checking Gas Funds (Required: 600000)...
[SmartAccount] Current Balance: 0
[SmartAccount] ⚠️ Insufficient funds. Shortage: 600000
[SmartAccount] 🔄 Auto-depositing 600000 USDC from EOA...
[SmartAccount] Deposit Tx Sent: 0xc145...
[SmartAccount] ✅ Deposit confirmed. Proceeding with UserOp.

✅ Transaction Submitted!
Tx Hash: https://basescan.org/tx/0xf976...
```
