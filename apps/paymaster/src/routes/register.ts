import { Router, Request, Response } from 'express';
import { verifyMessage } from 'viem';
import { getDbPool } from '../db';
import crypto from 'crypto';

const router = Router();

// Message that user must sign
const getSignMessage = (did: string, timestamp: number) =>
    `Register A2A Paymaster for ${did} at ${timestamp}`;

router.post('/register', async (req: Request, res: Response) => {
    try {
        const { did, signature, timestamp } = req.body;

        if (!did || !signature || !timestamp) {
            return res.status(400).json({ error: 'Missing did, signature, or timestamp' });
        }

        // 1. Verify Timestamp (prevent replay attacks, allow 5 min window)
        const now = Date.now();
        if (Math.abs(now - timestamp) > 5 * 60 * 1000) {
            return res.status(400).json({ error: 'Timestamp expired or invalid' });
        }

        // 2. Extract Address from DID (Assuming did:pkh or did:ethr)
        // Format: did:pkh:eip155:1:0x123... or did:ethr:0x123...
        // Simple extraction for MVP
        const parts = did.split(':');
        const addressPart = parts.find((p: string) => p.startsWith('0x'));

        if (!addressPart || addressPart.length !== 42) {
            return res.status(400).json({ error: 'Unsupported DID format. Must contain Ethereum address.' });
        }

        // 3. Verify Signature
        const message = getSignMessage(did, timestamp);
        const valid = await verifyMessage({
            address: addressPart as `0x${string}`,
            message: message,
            signature: signature as `0x${string}`,
        });

        if (!valid) {
            return res.status(401).json({ error: 'Invalid Signature' });
        }

        // 4. Generate API Key
        const apiKey = crypto.randomBytes(32).toString('hex');

        // 5. Store in DB
        const client = await getDbPool().connect();
        try {
            await client.query(
                `INSERT INTO api_keys (did, api_key) VALUES ($1, $2)
                 ON CONFLICT (did) DO UPDATE SET api_key = $2, updated_at = NOW()`,
                [did, apiKey]
            );
        } finally {
            client.release();
        }

        console.log(`✅ Registered API Key for DID: ${did}`);

        return res.json({
            success: true,
            did,
            apiKey,
            message: "Keep this key safe! It will not be shown again."
        });

    } catch (error: any) {
        console.error('Registration Error:', error);
        res.status(500).json({ error: 'Internal Server Error', details: error.message });
    }
});

export { router as registerRouter };
