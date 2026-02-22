import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
    isOverheated,
    getBaseDeposit,
    getDaimBalance,
    isAgentRegistered,
    getPendingTaskCount,
    getTask,
    publicClient,
    CONTRACTS
} from '../src/a2a-contracts.js';

describe('A2A Contracts Utilities', () => {
    beforeEach(() => {
        vi.spyOn(publicClient, 'readContract').mockReset();
    });

    it('should return overheated status', async () => {
        vi.spyOn(publicClient, 'readContract').mockResolvedValue(true);
        const result = await isOverheated();
        expect(publicClient.readContract).toHaveBeenCalledWith(expect.objectContaining({
            address: CONTRACTS.BUFFER,
            functionName: 'isOverheated'
        }));
        expect(result).toBe(true);
    });

    it('should return base deposit', async () => {
        vi.spyOn(publicClient, 'readContract').mockResolvedValue(100n);
        const result = await getBaseDeposit();
        expect(result).toBe(100n);
    });

    it('should return daim balance', async () => {
        vi.spyOn(publicClient, 'readContract').mockResolvedValue(500n);
        const address = '0x1234567890123456789012345678901234567890';
        const result = await getDaimBalance(address);
        expect(result).toBe(500n);
        expect(publicClient.readContract).toHaveBeenCalledWith(expect.objectContaining({
            address: CONTRACTS.DAIM,
            functionName: 'balanceOf',
            args: [address]
        }));
    });

    it('should return agent registration status', async () => {
        // Mock returning the structs where isRegistered is at index 4
        // The struct is: [metadataUrl, stakedAmount, resourceUnits, registeredAt, isRegistered, reputation, lastComplexityHash]
        vi.spyOn(publicClient, 'readContract').mockResolvedValue(['http...', 1n, 1n, 1000n, true, 50, 0n]);
        const address = '0x1234567890123456789012345678901234567890';
        const result = await isAgentRegistered(address);
        expect(result).toBe(true);
    });

    it('should return pending task count', async () => {
        vi.spyOn(publicClient, 'readContract').mockResolvedValue(42n);
        const result = await getPendingTaskCount();
        expect(result).toBe(42n);
    });

    it('should return task details', async () => {
        // Struct: id, complexityHash, deposit, exists, overheated, creator, submissionTime
        const mockTask = [1n, 123n, 10n, true, false, '0xcreator', 1000n];
        vi.spyOn(publicClient, 'readContract').mockResolvedValue(mockTask);
        const result = await getTask(1);
        expect(result).toEqual(mockTask);
    });
});
