# Paymaster Proxy Server Example

This example demonstrates how to build a secure backend service (API Provider) that sponsors transactions for its users without exposing the Paymaster API Key to the client side.

## Overview

1.  **Server (`src/server.ts`)**:
    *   Holds the `A2A_PAYMASTER_API_KEY` securely.
    *   Exposes an endpoint `POST /api/sponsor`.
    *   Validates requests (e.g. checks user authentication).
    *   Proxies the valid requests to the A2A Paymaster service.
    *   Returns the sponsorship data (`paymasterAndData`) to the client.

2.  **Client (`src/client.ts`)**:
    *   Constructs a UserOperation (UserOp).
    *   Instead of calling the Paymaster directly, it calls your Server.
    *    receives the sponsorship data and sends the transaction to the blockchain.

## Setup

1.  **Install Dependencies**:
    ```bash
    npm install
    ```

2.  **Configuration**:
    Create a `.env` file in this directory:
    ```bash
    # For the Server
    A2A_PAYMASTER_API_KEY="your-api-key-here"
    PAYMASTER_URL="https://paymaster.a10m.work/v1/paymaster"
    PORT=3000

    # For the Client (Test)
    PRIVATE_KEY="your-wallet-private-key"
    RPC_URL="https://mainnet.base.org"
    ```

## Running the Example

1.  **Start the Server**:
    Open a terminal and run:
    ```bash
    npm start
    ```
    You should see: `Server running at http://localhost:3000`

2.  **Run the Client**:
    Open a *new* terminal window and run:
    ```bash
    npm run client
    ```

    The client will:
    *   Generate a Smart Account address.
    *   Prepare a transaction (transferring 0.6 USDC fee + 0 ETH transfer).
    *   Request sponsorship from `http://localhost:3000/api/sponsor`.
    *   Submit the transaction to the network.
    *   Output the Transaction Hash.

## Key Code Highlights

### Server-Side Sponsorship
The server uses the SDK to fetch paymaster data:

```typescript
// src/server.ts
const paymasterManager = new PaymasterManager(PAYMASTER_URL, PAYMASTER_API_KEY);

app.post('/api/sponsor', async (req, res) => {
    // ... validate user ...
    const paymasterAndData = await paymasterManager.getPaymasterAndData(userOperation, chainId);
    res.json({ paymasterAndData });
});
```

### Client-Side Integration
The client uses a custom "Proxy Manager" to talk to your server:

```typescript
// src/client.ts
class ProxyPaymasterManager {
    constructor(private proxyUrl: string) {}

    async getPaymasterAndData(userOperation: any, chainId: number): Promise<string> {
        const response = await fetch(this.proxyUrl, {
             method: 'POST',
             body: JSON.stringify({ userOperation, chainId })
        });
        const data = await response.json();
        return data.paymasterAndData;
    }
}
```
