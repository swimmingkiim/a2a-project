import { createPublicClient, http, decodeEventLog, parseAbi, PublicClient, Transport, Chain } from 'viem';

const TRANSFER_EVENT_ABI = parseAbi(['event Transfer(address indexed from, address indexed to, uint256 value)']);

export interface PaymentVerificationResult {
    isValid: boolean;
    error?: string;
    txHash?: `0x${string}`;
    from?: `0x${string}`;
    to?: `0x${string}`;
    amount?: bigint;
}

export interface PaymentVerifierConfig {
    rpcUrl: string;
    chain: Chain;
    tokenAddress?: `0x${string}`; // Default: USDC on Base
}

/**
 * PaymentVerifier class for verifying ERC20 token payments on-chain.
 * Useful for implementing pay-per-use API access patterns.
 */
export class PaymentVerifier {
    private publicClient: PublicClient<Transport, Chain>;
    private tokenAddress: `0x${string}`;

    /**
     * Creates a new PaymentVerifier instance
     * @param config Configuration object with RPC URL, chain, and optional token address
     */
    constructor(config: PaymentVerifierConfig) {
        this.publicClient = createPublicClient({
            chain: config.chain,
            transport: http(config.rpcUrl)
        });

        // Default to USDC on Base if not specified
        this.tokenAddress = config.tokenAddress || '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
    }

    /**
     * Verifies that a specific ERC20 transfer transaction occurred
     * @param txHash Transaction hash to verify
     * @param expectedFrom Expected sender address
     * @param expectedTo Expected receiver address
     * @param minimumAmount Minimum amount that must have been transferred (in token base units)
     * @returns PaymentVerificationResult with verification status and details
     */
    async verifyPayment(
        txHash: `0x${string}`,
        expectedFrom: `0x${string}`,
        expectedTo: `0x${string}`,
        minimumAmount: bigint
    ): Promise<PaymentVerificationResult> {
        try {
            // 1. Get transaction receipt
            const receipt = await this.publicClient.getTransactionReceipt({ hash: txHash });

            if (!receipt) {
                return {
                    isValid: false,
                    error: 'Transaction not found'
                };
            }

            if (receipt.status !== 'success') {
                return {
                    isValid: false,
                    error: 'Transaction failed',
                    txHash
                };
            }

            // 2. Filter logs for the specified token contract
            const tokenLogs = receipt.logs.filter((log: any) =>
                log.address.toLowerCase() === this.tokenAddress.toLowerCase()
            );

            if (tokenLogs.length === 0) {
                return {
                    isValid: false,
                    error: 'No transfer events found for this token',
                    txHash
                };
            }

            // 3. Parse Transfer events and find matching one
            for (const log of tokenLogs) {
                try {
                    const decoded = decodeEventLog({
                        abi: TRANSFER_EVENT_ABI,
                        data: log.data,
                        topics: log.topics
                    });

                    const { from, to, value } = decoded.args as { from: `0x${string}`, to: `0x${string}`, value: bigint };

                    // Check if this transfer matches our criteria
                    if (
                        from.toLowerCase() === expectedFrom.toLowerCase() &&
                        to.toLowerCase() === expectedTo.toLowerCase() &&
                        value >= minimumAmount
                    ) {
                        return {
                            isValid: true,
                            txHash,
                            from,
                            to,
                            amount: value
                        };
                    }
                } catch (decodeError) {
                    // Skip logs that don't match Transfer event signature
                    continue;
                }
            }

            // No matching transfer found
            return {
                isValid: false,
                error: 'No matching transfer found in transaction',
                txHash
            };

        } catch (error: any) {
            return {
                isValid: false,
                error: error.message || 'Unknown error during verification'
            };
        }
    }

    /**
     * Convenience method for verifying USDC payments
     * @param txHash Transaction hash to verify
     * @param expectedFrom Expected sender address
     * @param expectedTo Expected receiver address
     * @param minimumUSDC Minimum USDC amount in base units (1 USDC = 1000000)
     */
    async verifyUSDCPayment(
        txHash: `0x${string}`,
        expectedFrom: `0x${string}`,
        expectedTo: `0x${string}`,
        minimumUSDC: bigint
    ): Promise<PaymentVerificationResult> {
        return this.verifyPayment(txHash, expectedFrom, expectedTo, minimumUSDC);
    }
}
