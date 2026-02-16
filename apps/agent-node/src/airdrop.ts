
import { createWalletClient, createPublicClient, http, parseAbi, parseEther, isAddress } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { baseSepolia } from 'viem/chains'; // Default to testnet, configurable

// Environment variables
const PRIVATE_KEY = process.env.AIRDROP_PRIVATE_KEY;
const RPC_URL = process.env.RPC_URL || 'https://sepolia.base.org';
const AIRDROP_AMOUNT = process.env.AIRDROP_AMOUNT || '10'; // 10 Tokens
const TOKEN_ADDRESS = process.env.AIRDROP_TOKEN_ADDRESS || '0x036CbD53842c5426634e7929541eC2318f3dCF7e'; // Default or Mock

// ERC20 ABI (Minimal)
const ERC20_ABI = parseAbi([
    'function transfer(address to, uint256 amount) returns (bool)',
    'function balanceOf(address account) view returns (uint256)',
    'function decimals() view returns (uint8)'
]);

export class AirdropService {
    private walletClient: any;
    private publicClient: any;
    private account: any;
    private enabled: boolean = false;

    constructor() {
        if (!PRIVATE_KEY) {
            console.warn('[Airdrop] AIRDROP_PRIVATE_KEY not set. Airdrop service disabled.');
            return;
        }

        try {
            this.account = privateKeyToAccount(PRIVATE_KEY as `0x${string}`);
            this.publicClient = createPublicClient({
                chain: baseSepolia,
                transport: http(RPC_URL)
            });
            this.walletClient = createWalletClient({
                account: this.account,
                chain: baseSepolia,
                transport: http(RPC_URL)
            });
            this.enabled = true;
            console.log(`[Airdrop] Service initialized. Wallet: ${this.account.address}`);
        } catch (error) {
            console.error('[Airdrop] Failed to initialize wallet:', error);
        }
    }

    isEnabled() {
        return this.enabled;
    }

    async sendAirdrop(to: string) {
        if (!this.enabled) {
            throw new Error('Airdrop service is disabled (Missing Private Key)');
        }

        if (!isAddress(to)) {
            throw new Error(`Invalid recipient address: ${to}`);
        }

        console.log(`[Airdrop] Sending ${AIRDROP_AMOUNT} tokens to ${to}...`);

        // Convert amount based on decimals (assuming 18, but ideally check)
        const amount = parseEther(AIRDROP_AMOUNT);

        try {
            const hash = await this.walletClient.writeContract({
                address: TOKEN_ADDRESS,
                abi: ERC20_ABI,
                functionName: 'transfer',
                args: [to, amount]
            });

            console.log(`[Airdrop] Tx Sent: ${hash}`);
            return hash;
        } catch (error: any) {
            console.error('[Airdrop] Transaction Failed:', error);
            throw new Error(`Airdrop Failed: ${error.message}`);
        }
    }

    async getBalance() {
        if (!this.enabled) return '0';
        try {
            const balance = await this.publicClient.readContract({
                address: TOKEN_ADDRESS,
                abi: ERC20_ABI,
                functionName: 'balanceOf',
                args: [this.account.address]
            });
            return balance.toString();
        } catch (error) {
            console.error('[Airdrop] Failed to fetch balance:', error);
            return 'Error';
        }
    }
}

export const airdropService = new AirdropService();
