import request from 'supertest';
import { app } from '../src/index';
import { encodeFunctionData, parseAbi, Hex } from 'viem';

// Mock config
jest.mock('../src/config', () => ({
    config: {
        PORT: 8080,
        UPSTREAM_PAYMASTER_URL: 'https://api.pimlico.io/v2/base/rpc',
        RPC_URL: 'https://mainnet.base.org',
        MARKUP_RATE: 0.1,
        TREASURY_ADDRESS: '0x1000000000000000000000000000000000000001', // Mock Treasury
        FEE_TOKEN_ADDRESS: '0x2000000000000000000000000000000000000002', // Mock Token
        FEE_AMOUNT: '100000', // 0.1 USDC (Floor)
        ETH_PRICE_USD: '2500', // $2500 / ETH
        MARKUP_RATE: 0.1, // 10%
        A2A_PAYMASTER_API_KEY: 'test-api-key',
        DB_HOST: undefined // Disable DB to avoid init
    }
}));

const ERC20_ABI = parseAbi(['function transfer(address to, uint256 amount) returns (bool)']);
const BATCH_EXECUTE_ABI = parseAbi(['function executeBatch(address[] dest, uint256[] value, bytes[] func)']);
const EXECUTE_ABI = parseAbi(['function execute(address target, uint256 value, bytes calldata data)']);
const SAFE_EXEC_ABI = parseAbi([
    'function execTransaction(address to, uint256 value, bytes data, uint8 operation, uint256 safeTxGas, uint256 baseGas, uint256 gasPrice, address gasToken, address refundReceiver, bytes signatures)'
]);

// Mock viem
// Mock viem
jest.mock('viem', () => {
    const originalModule = jest.requireActual('viem');
    return {
        __esModule: true,
        ...originalModule,
        createPublicClient: jest.fn(() => ({
            readContract: jest.fn().mockImplementation(async (args) => {
                // Heuristic: If args has no functionName or it looks like balance/default, return large
                // If it looks like L1 fee, return small
                const str = JSON.stringify(args || {});
                if (str.includes('getL1Fee')) {
                    return 100n;
                }
                return 1000000000000000000n;
            }),
            getGasPrice: jest.fn().mockResolvedValue(1000000000n), // 1 Gwei
        })),
        http: jest.fn(),
    };
});

describe('Fee Validation', () => {

    it('[PASS] Should accept UserOp with valid fee transfer (Batch)', async () => {
        // Construct valid callData
        const feeTransferData = encodeFunctionData({
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: ['0x1000000000000000000000000000000000000001', 100000n]
        });

        // Mock a batch execute call
        const callData = encodeFunctionData({
            abi: BATCH_EXECUTE_ABI,
            functionName: 'executeBatch',
            args: [
                ['0x2000000000000000000000000000000000000002', '0x3000000000000000000000000000000000000003'], // dest: Fee Token, Other
                [0n, 0n], // value
                [feeTransferData, '0x'] // func: transfer(treasury, amount), other
            ]
        });

        // Mock Upstream Response
        const fetchMock = jest.spyOn(global, 'fetch').mockResolvedValue({
            ok: true,
            json: async () => ({ jsonrpc: '2.0', id: 1, result: { preVerificationGas: '0x1' } })
        } as Response);


        const res = await request(app)
            .post('/v1/paymaster')
            .set('x-api-key', 'test-api-key')
            .send({
                jsonrpc: '2.0',
                method: 'pm_sponsorUserOperation',
                params: [{ sender: '0x123', callData: callData }],
                id: 1
            });

        expect(res.status).toBe(200);
        expect(res.body.result).toBeDefined();

        fetchMock.mockRestore();
    });

    it('[PASS] Should accept UserOp with valid fee transfer (Single Execute)', async () => {
        // Construct valid callData (direct call to token)
        const feeTransferData = encodeFunctionData({
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: ['0x1000000000000000000000000000000000000001', 100000n]
        });

        // Mock execute call
        const callData = encodeFunctionData({
            abi: EXECUTE_ABI,
            functionName: 'execute',
            args: [
                '0x2000000000000000000000000000000000000002', // target: Fee Token
                0n, // value
                feeTransferData // data
            ]
        });

        const fetchMock = jest.spyOn(global, 'fetch').mockResolvedValue({
            ok: true,
            json: async () => ({ jsonrpc: '2.0', id: 1, result: { preVerificationGas: '0x1' } })
        } as Response);

        const res = await request(app)
            .post('/v1/paymaster')
            .set('x-api-key', 'test-api-key')
            .send({
                jsonrpc: '2.0',
                method: 'pm_sponsorUserOperation',
                params: [{ sender: '0x123', callData: callData }],
                id: 1
            });

        expect(res.status).toBe(200);
        expect(res.body.result).toBeDefined();

        fetchMock.mockRestore();
    });

    it('[PASS] Should accept UserOp with valid fee transfer (Safe execTransaction)', async () => {
        // Construct valid fee transfer data
        const feeTransferData = encodeFunctionData({
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: ['0x1000000000000000000000000000000000000001', 100000n]
        });

        // Mock Safe execTransaction call
        const callData = encodeFunctionData({
            abi: SAFE_EXEC_ABI,
            functionName: 'execTransaction',
            args: [
                '0x2000000000000000000000000000000000000002', // to: Fee Token
                0n, // value
                feeTransferData, // data
                0, // operation
                0n, 0n, 0n, // gas
                '0x0000000000000000000000000000000000000000', // gasToken
                '0x0000000000000000000000000000000000000000', // refundReceiver
                '0x' // signatures
            ]
        });

        const fetchMock = jest.spyOn(global, 'fetch').mockResolvedValue({
            ok: true,
            json: async () => ({ jsonrpc: '2.0', id: 1, result: { preVerificationGas: '0x1' } })
        } as Response);

        const res = await request(app)
            .post('/v1/paymaster')
            .set('x-api-key', 'test-api-key')
            .send({
                jsonrpc: '2.0',
                method: 'pm_sponsorUserOperation',
                params: [{ sender: '0x123', callData: callData }],
                id: 1
            });

        expect(res.status).toBe(200);
        expect(res.body.result).toBeDefined();

        fetchMock.mockRestore();
    });

    it('[PASS] Should accept UserOp with Sufficient Dynamic Fee (High Gas)', async () => {
        // High Gas Usage Scenario
        // Gas: 500,000 total
        // Price: 1 gwei (1e9 wei)
        // Cost: 500,000 * 1e9 = 5e14 wei = 0.0005 ETH
        // Price: $2500
        // Value: 0.0005 * 2500 = $1.25
        // Markup: 1.1x
        // Required: $1.375
        // USDC (6 dec): 1,375,000

        const feeAmount = 1400000n; // $1.40 (Sufficient)

        const feeTransferData = encodeFunctionData({
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: ['0x1000000000000000000000000000000000000001', feeAmount]
        });

        const callData = encodeFunctionData({
            abi: EXECUTE_ABI,
            functionName: 'execute',
            args: [
                '0x2000000000000000000000000000000000000002',
                0n,
                feeTransferData
            ]
        });

        const fetchMock = jest.spyOn(global, 'fetch').mockResolvedValue({
            ok: true,
            json: async () => ({ jsonrpc: '2.0', id: 1, result: { preVerificationGas: '0x1' } })
        } as Response);

        const res = await request(app)
            .post('/v1/paymaster')
            .set('x-api-key', 'test-api-key')
            .send({
                jsonrpc: '2.0',
                method: 'pm_sponsorUserOperation',
                params: [{
                    sender: '0x123',
                    callData: callData,
                    // Gas params acting as high cost
                    verificationGasLimit: '0x30D40', // 200,000
                    callGasLimit: '0x30D40', // 200,000
                    preVerificationGas: '0x186A0', // 100,000
                    maxFeePerGas: '0x3B9ACA00', // 1 Gwei
                    maxPriorityFeePerGas: '0x3B9ACA00'
                }],
                id: 1
            });

        expect(res.status).toBe(200);
        expect(res.body.result).toBeDefined();

        fetchMock.mockRestore();
    });

    it('[FAIL] Should reject UserOp with Insufficient Dynamic Fee', async () => {
        // Same scenario, but fee is only floor ($0.10)
        // Required: ~$1.375

        const feeAmount = 100000n; // $0.10 (Insufficient)

        const feeTransferData = encodeFunctionData({
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: ['0x1000000000000000000000000000000000000001', feeAmount]
        });

        const callData = encodeFunctionData({
            abi: EXECUTE_ABI,
            functionName: 'execute',
            args: [
                '0x2000000000000000000000000000000000000002',
                0n,
                feeTransferData
            ]
        });

        const res = await request(app)
            .post('/v1/paymaster')
            .set('x-api-key', 'test-api-key')
            .send({
                jsonrpc: '2.0',
                method: 'pm_sponsorUserOperation',
                params: [{
                    sender: '0x123',
                    callData: callData,
                    // Gas params acting as high cost
                    verificationGasLimit: '0x30D40', // 200,000
                    callGasLimit: '0x30D40', // 200,000
                    preVerificationGas: '0x186A0', // 100,000
                    maxFeePerGas: '0x3B9ACA00', // 1 Gwei
                    maxPriorityFeePerGas: '0x3B9ACA00'
                }],
                id: 1
            });

        expect(res.status).toBe(403); // Forbidden
        // Note: The error message might just be "Missing Treasury Fee Transfer" or similar
        // since our logic just returns false if check failed.
    });

    it('[FAIL] Should reject UserOp without fee transfer', async () => {
        const callData = '0x'; // Empty callData or other function

        const res = await request(app)
            .post('/v1/paymaster')
            .set('x-api-key', 'test-api-key')
            .send({
                jsonrpc: '2.0',
                method: 'pm_sponsorUserOperation',
                params: [{ sender: '0x123', callData: callData }],
                id: 1
            });

        expect(res.status).toBe(403);
        expect(res.body.error.message).toContain('Missing Treasury Fee Transfer');
    });

    it('[PASS] Should ignore fee check for non-sponsorship methods', async () => {
        const mockUpstreamResponse = { jsonrpc: '2.0', id: 1, result: '0x1' };
        const fetchMock = jest.spyOn(global, 'fetch').mockResolvedValue({
            ok: true,
            json: async () => mockUpstreamResponse,
            text: async () => JSON.stringify(mockUpstreamResponse)
        } as Response);

        const res = await request(app)
            .post('/v1/paymaster')
            .set('x-api-key', 'test-api-key')
            .send({
                jsonrpc: '2.0',
                method: 'eth_estimateUserOperationGas',
                params: [{ sender: '0x123', callData: '0x' }],
                id: 1
            });

        expect(res.status).toBe(200);
        expect(res.body.error).toBeUndefined();

        fetchMock.mockRestore();
    });
});
