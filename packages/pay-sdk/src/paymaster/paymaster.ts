import { createPimlicoClient } from "permissionless/clients/pimlico"
import { http, encodeFunctionData, parseAbi, Hex } from "viem"

const ERC20_ABI = parseAbi(['function transfer(address to, uint256 amount) returns (bool)']);


/**
 * Fee configuration for PaymasterManager
 */
export interface FeeConfig {
    treasury: string;
    amount: bigint;
    tokenType: 'USDC' | 'DAIM';
    tokenAddress?: string; // Optional override for custom token address
}

export class PaymasterManager {
    private client: any
    private apiKey?: string

    constructor(rpcUrl: string = "http://localhost:8080/v1/paymaster", apiKey?: string) {
        this.apiKey = apiKey;
        const fetchOptions = apiKey ? { headers: { 'x-api-key': apiKey } } : undefined;

        this.client = createPimlicoClient({
            transport: http(rpcUrl, { fetchOptions }),
            entryPoint: {
                address: '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789',
                version: '0.6',
            }
        })
    }

    getClient() {
        return this.client
    }

    getApiKey() {
        return this.apiKey;
    }

    async getStubPaymasterData(userOp: any) {
        return this.client.sponsorUserOperation({
            userOperation: userOp
        })
    }

    /**
     * Appends a fee transfer transaction to the list of calls.
     * 
     * Supports dual-token economy: USDC (default) or DAIM.
     * 
     * @param calls Array of transaction calls { to, value, data }
     * @param feeConfig Configuration for the fee
     * @returns New array of calls with the fee transaction appended
     * 
     * @example
     * // USDC fee (legacy)
     * const calls = PaymasterManager.appendFeeToCalls([], {
     *   treasury: '0x...',
     *   amount: 100000n,  // 0.1 USDC (6 decimals)
     *   tokenType: 'USDC'
     * });
     * 
     * @example
     * // DAIM fee (new)
     * const calls = PaymasterManager.appendFeeToCalls([], {
     *   treasury: '0x...',
     *   amount: 25n * 10n**18n,  // 25 DAIM (18 decimals)
     *   tokenType: 'DAIM'
     * });
     */
    static TOKEN_ADDRESSES: Record<string, string> = {
        'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', // USDC on Base
        'DAIM': '0xED175F6ff582318b6DC16FE76e8B5CA7F8fB3Ce3',  // DaimToken on Base Sepolia
    };


    static appendFeeToCalls(calls: any[], feeConfig: FeeConfig) {
        // Use custom address if provided, otherwise use default from static map
        const tokenAddress = feeConfig.tokenAddress || PaymasterManager.TOKEN_ADDRESSES[feeConfig.tokenType];

        if (!tokenAddress) {
            throw new Error(`Token address not found for type: ${feeConfig.tokenType}. Please provide tokenAddress in config or update PaymasterManager.TOKEN_ADDRESSES.`);
        }

        if (feeConfig.treasury === '0x0000000000000000000000000000000000000000') {
            console.warn("PaymasterManager: Treasury address is not set. Fee transaction might fail validation.");
        }

        const feeCall = {
            to: tokenAddress as Hex,
            value: 0n,
            data: encodeFunctionData({
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [feeConfig.treasury as Hex, feeConfig.amount]
            })
        };

        return [...calls, feeCall];
    }
}
