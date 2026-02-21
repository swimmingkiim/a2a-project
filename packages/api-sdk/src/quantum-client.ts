import { createPublicClient, http, getContract, Address, PublicClient } from 'viem';

const QUANTUM_TASK_BUFFER_ABI = [
    {
        "inputs": [],
        "name": "isOverheated",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_complexityHash",
                "type": "uint256"
            },
            {
                "internalType": "string",
                "name": "_metadataUri",
                "type": "string"
            }
        ],
        "name": "submitTask",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
] as const;

export interface QuantumClientOptions {
    rpcUrl: string;
    contractAddress: Address;
    baseBackoffMs?: number;
    maxBackoffMs?: number;
    maxRetries?: number;
}

export class OverheatedError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'OverheatedError';
    }
}

/**
 * Client for interacting with the QuantumTaskBuffer smart contract.
 * Implements V_AI (Self-Restraint) by structurally enforcing an exponential backoff
 * when the macroscopic system is detected as 'overheated'.
 */
export class QuantumTaskClient {
    private publicClient: PublicClient;
    private contractAddress: Address;
    private baseBackoffMs: number;
    private maxBackoffMs: number;
    private maxRetries: number;

    constructor(options: QuantumClientOptions) {
        this.publicClient = createPublicClient({
            transport: http(options.rpcUrl),
        });
        this.contractAddress = options.contractAddress;
        this.baseBackoffMs = options.baseBackoffMs || 30_000; // 30 seconds default
        this.maxBackoffMs = options.maxBackoffMs || 600_000;  // 10 mins default
        this.maxRetries = options.maxRetries || 5;
    }

    /**
     * Checks the thermodynamic state of the buffer.
     * @returns boolean true if the system pending tasks exceed CRITICAL_MASS.
     */
    async isOverheated(): Promise<boolean> {
        const contract = getContract({
            address: this.contractAddress,
            abi: QUANTUM_TASK_BUFFER_ABI,
            client: this.publicClient
        });

        try {
            return await contract.read.isOverheated() as boolean;
        } catch (error) {
            console.error("Failed to read isOverheated state from contract:", error);
            throw new Error("Failed to check thermodynamic state. Assuming overheated for safety.");
        }
    }

    /**
     * Sleep helper for backoff
     */
    private sleep(ms: number) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Prepares the `submitTask` transaction call data, enforcing V_AI (Thermodynamic Throttling).
     * The agent SDK intrinsically checks the `isOverheated` state. If the system is overheated,
     * the SDK *refuses* to generate the transaction and applies an exponential backoff.
     * 
     * @param complexityHash The unique hash of the task logic to submit.
     * @param metadataUri The URI (e.g. ipfs://...) pointing to the standard JSON metadata.
     * @returns The call data object for use with the Paymaster or standard transaction execution.
     * @throws OverheatedError if max retries are exceeded while the system remains overheated.
     */
    async enforceThrottleAndGetTaskCall(complexityHash: bigint, metadataUri: string): Promise<{ to: Address, value: bigint, data: string }> {
        let attempt = 0;
        let currentBackoff = this.baseBackoffMs;

        while (attempt < this.maxRetries) {
            const overheated = await this.isOverheated();

            if (!overheated) {
                // System is safe, generate the transaction call data

                // Note: the actual submission is usually done via Paymaster/UserOp, 
                // so we return the raw call data to be appended.


                // Using generic approach to format call data for viem
                const { encodeFunctionData } = await import('viem');
                const encodedData = encodeFunctionData({
                    abi: QUANTUM_TASK_BUFFER_ABI,
                    functionName: 'submitTask',
                    args: [complexityHash, metadataUri]
                });

                return {
                    to: this.contractAddress,
                    value: 0n,
                    data: encodedData
                };
            }

            console.warn(`[V_AI Throttling] System is OVERHEATED. Attempt ${attempt + 1}/${this.maxRetries}. Backing off for ${currentBackoff}ms...`);

            await this.sleep(currentBackoff);

            // Exponential backoff with jitter
            attempt++;
            const jitter = Math.random() * 0.2 + 0.9; // 0.9 - 1.1 multiplier
            currentBackoff = Math.min(currentBackoff * 2 * jitter, this.maxBackoffMs);
        }

        throw new OverheatedError("System critically overheated. Task submission aborted after max retries to preserve macro-economic stability.");
    }
}
