import express from 'express';
import cors from 'cors';
import { config } from 'dotenv';
import { PaymasterManager, PaymentVerifier } from '@swimmingkiim/pay-sdk';
import { base } from 'viem/chains';

// Load environment variables
config();

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Paymaster Manager with server-side API Key
const PAYMASTER_URL = process.env.PAYMASTER_URL || 'https://paymaster.a10m.work/v1/paymaster';
const PAYMASTER_API_KEY = process.env.A2A_PAYMASTER_API_KEY;

if (!PAYMASTER_API_KEY) {
    console.warn("⚠️  WARNING: A2A_PAYMASTER_API_KEY is not set. Sponsorship requests may fail.");
}

const paymasterManager = new PaymasterManager(PAYMASTER_URL, PAYMASTER_API_KEY);

app.use(cors());
app.use(express.json());

// --- Generic RPC Proxy (for Bundler methods) ---
app.post('/rpc', async (req, res) => {
    try {
        const { method, params, id, jsonrpc } = req.body;
        console.log(`[RPC Proxy] Method: ${method}`);

        // Proxy all requests to the real Paymaster with the API key injected
        const response = await fetch(PAYMASTER_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': PAYMASTER_API_KEY as string
            },
            body: JSON.stringify(req.body)
        });

        const data = await response.json();
        res.json(data);

    } catch (error: any) {
        console.error("RPC Proxy failed:", error.message);
        res.status(500).json({ error: 'RPC Proxy failed', details: error.message });
    }
});

// --- Paymaster Proxy Endpoint ---
app.post('/api/sponsor', async (req, res) => {
    try {
        const { userOperation, chainId } = req.body;

        if (!userOperation || !chainId) {
            return res.status(400).json({ error: 'Missing userOperation or chainId' });
        }

        console.log(`Received sponsorship request for chain ${chainId}`);

        // TODO: Implement your own authentication/authorization logic here.
        // For example, verify a session token, check user subscription status, etc.
        // if (!req.user.isPremium) throw new Error("User not eligible for sponsorship");

        // Request sponsorship from the legitimate Paymaster service
        // using the secure API Key stored on this server.
        // @ts-ignore
        const paymasterAndData = await paymasterManager.getStubPaymasterData(userOperation);

        console.log("Sponsorship successful!");

        // Return the sponsorship result to the client
        res.json({ paymasterAndData });

    } catch (error: any) {
        console.error("Sponsorship failed:", error.message);
        res.status(500).json({ error: 'Sponsorship failed', details: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
    console.log(`Paymaster URL: ${PAYMASTER_URL}`);
});
