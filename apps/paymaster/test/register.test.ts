import request from 'supertest';
import { app } from '../src/index';
import { generatePrivateKey, privateKeyToAccount } from 'viem/accounts';
// We don't import verifyMessage here, we just use it implicitly via app

// Mock Config
jest.mock('../src/config', () => ({
    config: {
        PORT: 8080,
        // Mock private key for airdrop
        PAYMASTER_SIGNER_PRIVATE_KEY: '0x0000000000000000000000000000000000000000000000000000000000000001',
        DAIM_TOKEN_ADDRESS: '0xDAIMTOKEN',
        RPC_URL: 'https://mock.rpc',
        NODE_ENV: 'test'
    }
}));

// Mock DB
jest.mock('../src/db', () => ({
    getDbPool: () => ({
        connect: jest.fn().mockResolvedValue({
            query: jest.fn().mockResolvedValue({}),
            release: jest.fn()
        })
    })
}));

// Mock Viem
const mockWriteContract = jest.fn().mockResolvedValue('0xTxHash');
jest.mock('viem', () => {
    const original = jest.requireActual('viem');
    return {
        __esModule: true,
        ...original,
        createWalletClient: () => {
            return {
                writeContract: jest.fn().mockResolvedValue('0xTxHash'),
                extend: jest.fn()
            };
        },
        createPublicClient: () => ({}),
        http: jest.fn(),
    };
});

import { createWalletClient } from 'viem';



describe('Registration API Verification', () => {

    // Generate a real identity for testing
    const privateKey = generatePrivateKey();
    const account = privateKeyToAccount(privateKey);
    const did = `did:pkh:eip155:1:${account.address}`;

    const generatePayload = async (apiUrl?: string) => {
        const timestamp = Date.now();
        const message = `Register A2A Paymaster for ${did} at ${timestamp}`;
        const signature = await account.signMessage({ message });
        return {
            did,
            signature,
            timestamp,
            apiUrl
        };
    };

    let fetchMock: jest.SpyInstance;

    beforeEach(() => {
        fetchMock = jest.spyOn(global, 'fetch');
        mockWriteContract.mockClear();
    });

    afterEach(() => {
        fetchMock.mockRestore();
    });

    it('[FAIL] Should reject non-HTTPS URL', async () => {
        const payload = await generatePayload('http://example.com');
        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('URL must start with https://');
    });

    it('[FAIL] Should reject if Root returns 404', async () => {
        fetchMock.mockResolvedValueOnce({ ok: false, status: 404 } as Response); // Root check

        const payload = await generatePayload('https://example.com');
        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('Root https://example.com/ returned 404');
    });

    it('[FAIL] Should reject if llms.txt is missing', async () => {
        fetchMock
            .mockResolvedValueOnce({ ok: true } as Response) // Root
            .mockResolvedValueOnce({ ok: false, status: 404 } as Response); // llms.txt

        const payload = await generatePayload('https://example.com');
        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('llms.txt at https://example.com/llms.txt returned 404');
    });

    it('[FAIL] Should reject if manifest is missing', async () => {
        fetchMock
            .mockResolvedValueOnce({ ok: true } as Response) // Root
            .mockResolvedValueOnce({ ok: true, text: async () => 'Rules...' } as Response) // llms.txt
            .mockResolvedValueOnce({ ok: false, status: 404 } as Response); // manifest

        const payload = await generatePayload('https://example.com');
        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('Manifest at https://example.com/.well-known/ai-plugin.json returned 404');
    });

    it('[FAIL] Should reject if manifest is invalid (missing fields)', async () => {
        fetchMock
            .mockResolvedValueOnce({ ok: true } as Response) // Root
            .mockResolvedValueOnce({ ok: true, text: async () => 'Rules...' } as Response) // llms.txt
            .mockResolvedValueOnce({ ok: true, json: async () => ({ name_for_human: 'Bot' }) } as Response); // Manifest missing api

        const payload = await generatePayload('https://example.com');
        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('Manifest missing field: description_for_human');
    });

    it('[FAIL] Should reject if API spec is unreachable', async () => {
        fetchMock
            .mockResolvedValueOnce({ ok: true } as Response) // Root
            .mockResolvedValueOnce({ ok: true, text: async () => 'Rules...' } as Response) // llms.txt
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    name_for_human: 'Bot',
                    description_for_human: 'Desc',
                    api: { url: 'https://example.com/openapi.yaml' }
                })
            } as Response) // Manifest
            .mockResolvedValueOnce({ ok: false, status: 500 } as Response); // Spec check

        const payload = await generatePayload('https://example.com');
        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(400);
        expect(res.body.error).toContain('OpenAPI spec at https://example.com/openapi.yaml unreachable');
    });

    it('[PASS] Should register and airdrop if all checks pass', async () => {
        fetchMock
            .mockResolvedValueOnce({ ok: true } as Response) // Root
            .mockResolvedValueOnce({ ok: true, text: async () => 'Rules...' } as Response) // llms.txt
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    name_for_human: 'Bot',
                    description_for_human: 'Desc',
                    api: { url: 'https://example.com/openapi.yaml' }
                })
            } as Response) // Manifest
            .mockResolvedValueOnce({ ok: true, text: async () => 'openapi: 3.0.0 ...' } as Response); // Spec check

        const payload = await generatePayload('https://example.com');
        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(200);
        expect(res.body.success).toBe(true);
        expect(res.body.airdropTx).toBe('0xTxHash');
    });

    it('[PASS] Should register without airdrop if apiUrl missing', async () => {
        // We need a fresh did or signature or strict validation might fail in real DB if conflict
        // But we mock DB so it's fine.
        const payload = await generatePayload(undefined);

        const res = await request(app)
            .post('/v1/register')
            .send(payload);

        expect(res.status).toBe(200);
        expect(res.body.success).toBe(true);
        expect(res.body.airdropTx).toBeUndefined(); // No airdrop
        expect(mockWriteContract).not.toHaveBeenCalled();
    });

});
