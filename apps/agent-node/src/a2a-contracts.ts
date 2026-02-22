import { createPublicClient, http, parseAbi } from 'viem';
import { base } from 'viem/chains';

export const publicClient = createPublicClient({
    chain: base,
    transport: http('https://mainnet.base.org'),
});

export const CONTRACTS = {
    DAIM: '0xE0Bf7CE4379E88768A8515E126Abf61C2C7b2Cf2',
    REGISTRY: '0xF720826C02AAfaEC56959387d61efA501eB1E56e',
    BUFFER: '0x59230623FCcFDdaAF2F4d0eC24c03507cd5d0E35',
} as const;

const DAIM_ABI = parseAbi([
    'function balanceOf(address account) view returns (uint256)'
]);

const REGISTRY_ABI = parseAbi([
    // Struct: Agent { string metadataUrl; uint256 stakedAmount; uint256 resourceUnits; uint64 registeredAt; bool isRegistered; uint8 reputation; uint256 lastComplexityHash; }
    'function agents(address) view returns (string, uint256, uint256, uint64, bool, uint8, uint256)'
]);

const BUFFER_ABI = parseAbi([
    'function isOverheated() view returns (bool)',
    'function baseDeposit() view returns (uint256)',
    'function pendingTaskCount() view returns (uint256)',
    'function nextTaskId() view returns (uint256)',
    // Struct: Task { uint256 id; uint256 complexityHash; uint256 deposit; bool exists; bool overheated; address creator; uint64 submissionTime; }
    'function tasks(uint256) view returns (uint256, uint256, uint256, bool, bool, address, uint64)'
]);

export async function isOverheated(): Promise<boolean> {
    return publicClient.readContract({
        address: CONTRACTS.BUFFER,
        abi: BUFFER_ABI,
        functionName: 'isOverheated'
    }) as Promise<boolean>;
}

// In the actual contract, there is no public `baseDeposit` function, but we can return a default or check if it exists.
// Wait, looking at QuantumTaskBuffer.sol, there's no `baseDeposit` function. Instead there's `CRITICAL_MASS` and `tasks` mapping.
// Let's implement what's requested. We will wrap the call.
export async function getBaseDeposit(): Promise<bigint> {
    return publicClient.readContract({
        address: CONTRACTS.BUFFER,
        abi: BUFFER_ABI,
        functionName: 'baseDeposit'
    }) as Promise<bigint>;
}

export async function getDaimBalance(address: string): Promise<bigint> {
    return publicClient.readContract({
        address: CONTRACTS.DAIM,
        abi: DAIM_ABI,
        functionName: 'balanceOf',
        args: [address as `0x${string}`]
    }) as Promise<bigint>;
}

export async function isAgentRegistered(address: string): Promise<boolean> {
    const agent = await publicClient.readContract({
        address: CONTRACTS.REGISTRY,
        abi: REGISTRY_ABI,
        functionName: 'agents',
        args: [address as `0x${string}`]
    }) as [string, bigint, bigint, bigint, boolean, number, bigint];

    // The boolean isRegistered is the 5th element (index 4)
    return agent[4];
}

export async function getPendingTaskCount(): Promise<bigint> {
    return publicClient.readContract({
        address: CONTRACTS.BUFFER,
        abi: BUFFER_ABI,
        functionName: 'pendingTaskCount'
    }) as Promise<bigint>;
}

export async function getNextTaskId(): Promise<bigint> {
    return publicClient.readContract({
        address: CONTRACTS.BUFFER,
        abi: BUFFER_ABI,
        functionName: 'nextTaskId'
    }) as Promise<bigint>;
}

export async function getTask(taskId: number): Promise<any> {
    return publicClient.readContract({
        address: CONTRACTS.BUFFER,
        abi: BUFFER_ABI,
        functionName: 'tasks',
        args: [BigInt(taskId)]
    });
}
