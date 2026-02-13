import { describe, it, expect, vi, beforeEach } from 'vitest'
import { SmartAccountManager } from '../src/account/smart-account.js'
import { privateKeyToAccount } from 'viem/accounts'
import { baseSepolia } from 'viem/chains'

describe('SmartAccountManager: Auto Deposit', () => {
    let sa: SmartAccountManager;
    let mockPublicClient: any;
    let mockWalletClient: any;
    let mockSigner: any;

    beforeEach(() => {
        mockSigner = privateKeyToAccount('0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80');

        mockWalletClient = {
            account: mockSigner,
            chain: baseSepolia,
            writeContract: vi.fn().mockResolvedValue('0xdepositHash')
        };

        mockPublicClient = {
            readContract: vi.fn(),
            waitForTransactionReceipt: vi.fn().mockResolvedValue({ status: 'success' }),
            estimateFeesPerGas: vi.fn().mockResolvedValue({ maxFeePerGas: 10n, maxPriorityFeePerGas: 1n })
        };

        sa = new SmartAccountManager(
            mockWalletClient,
            mockPublicClient,
            'http://localhost:8545'
        );

        // Mock initialized account manually since we are not calling createSafeAccount
        sa.account = { address: '0xSmartAccountAddress' };
        // Mock the permissionless client
        sa.client = {
            sendTransaction: vi.fn().mockResolvedValue('0xuserOpHash')
        };
    });

    it('should proceed if Smart Account has sufficient funds', async () => {
        // Mock Balance: SA = 1 USDC (1000000), Required = 0.6 USDC (600000)
        // First call is checking SA balance
        mockPublicClient.readContract.mockResolvedValueOnce(1000000n);

        await sa.executeBatch([]);

        expect(mockPublicClient.readContract).toHaveBeenCalledTimes(1); // Only checked SA balance
        expect(mockWalletClient.writeContract).not.toHaveBeenCalled(); // No deposit
        expect(sa.client.sendTransaction).toHaveBeenCalled();
    });

    it('should deposit from EOA if Smart Account has insufficient funds', async () => {
        // First call: SA Balance = 0
        mockPublicClient.readContract.mockResolvedValueOnce(0n);
        // Second call: EOA Balance = 1 USDC
        mockPublicClient.readContract.mockResolvedValueOnce(1000000n);

        await sa.executeBatch([]);

        expect(mockPublicClient.readContract).toHaveBeenCalledTimes(2); // Checked both
        expect(mockWalletClient.writeContract).toHaveBeenCalledWith(expect.objectContaining({
            functionName: 'transfer',
            args: ['0xSmartAccountAddress', 600000n] // Shortage is full amount (600000 - 0)
        }));
        expect(mockPublicClient.waitForTransactionReceipt).toHaveBeenCalled();
        expect(sa.client.sendTransaction).toHaveBeenCalled();
    });

    it('should throw if both have insufficient funds', async () => {
        // First call: SA Balance = 0
        mockPublicClient.readContract.mockResolvedValueOnce(0n);
        // Second call: EOA Balance = 0
        mockPublicClient.readContract.mockResolvedValueOnce(0n);

        await expect(sa.executeBatch([])).rejects.toThrow(/Insufficient funds/);

        expect(mockWalletClient.writeContract).not.toHaveBeenCalled();
        expect(sa.client.sendTransaction).not.toHaveBeenCalled();
    });

    it('should deposit partial shortage if partial funds exist', async () => {
        // Required: 600000
        // SA Balance: 40000
        // Shortage: 560000

        mockPublicClient.readContract.mockResolvedValueOnce(40000n); // SA
        mockPublicClient.readContract.mockResolvedValueOnce(1000000n); // EOA

        await sa.executeBatch([]);

        expect(mockWalletClient.writeContract).toHaveBeenCalledWith(expect.objectContaining({
            args: ['0xSmartAccountAddress', 560000n]
        }));
    });
});
