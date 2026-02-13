
import { createSmartAccountClient } from "permissionless"

import { type Account, type Address, type Chain, type Transport, type WalletClient, type PublicClient, http } from "viem"
import { toSafeSmartAccount } from "permissionless/accounts"
import { erc7579Actions } from "permissionless/actions/erc7579"

import { PaymasterManager } from "../paymaster/paymaster.js"

export class SmartAccountManager {
    public client: any
    public account: any

    constructor(
        private signer: WalletClient<Transport, Chain, Account>,
        private publicClient: PublicClient<Transport, Chain>,
        private rpcUrl: string,
        private paymaster?: PaymasterManager
    ) { }

    async createSafeAccount(saltNonce: bigint = 0n) {
        // Create 7579-compatible Safe Account
        this.account = await toSafeSmartAccount({
            client: this.publicClient,
            owners: [this.signer.account],
            version: '1.4.1',
            entryPoint: {
                address: '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789', // EntryPoint 0.6
                version: '0.6',
            },
            saltNonce,
        })

        const apiKey = this.paymaster?.getApiKey();
        const fetchOptions = apiKey ? { headers: { 'x-api-key': apiKey } } : undefined;

        this.client = createSmartAccountClient({
            account: this.account,
            chain: this.signer.chain,
            bundlerTransport: http(this.rpcUrl, { fetchOptions }),
            paymaster: this.paymaster ? this.paymaster.getClient() : undefined,
            userOperation: {
                estimateFeesPerGas: async () => {
                    const fees = await this.publicClient.estimateFeesPerGas();
                    return {
                        maxFeePerGas: ((fees.maxFeePerGas ?? 0n) * 20n) / 10n, // 2x (safety margin)
                        maxPriorityFeePerGas: ((fees.maxPriorityFeePerGas ?? 0n) * 20n) / 10n
                    } as any;
                }
            }
        }).extend(erc7579Actions())

        return this.account.address
    }

    getAddress(): Address {
        return this.account.address
    }

    async executeBatch(calls: { to: Address, value: bigint, data: `0x${string}` }[]) {
        if (!this.client) throw new Error("Account not initialized")

        // [Fee Logic] Ensure Smart Account has enough USDC for the fee
        // We assume 0.6 USDC is required per transaction (matching Paymaster Policy)
        await this.ensureGasFunds(600000n);

        const txHash = await this.client.sendTransaction({
            calls: calls,
            account: this.account
        })

        return txHash
    }

    // New Helper: Check and Deposit Funds if needed
    async ensureGasFunds(requiredAmount: bigint) {
        const USDC_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
        const ERC20_ABI = [{
            name: 'balanceOf',
            type: 'function',
            stateMutability: 'view',
            inputs: [{ name: 'account', type: 'address' }],
            outputs: [{ name: '', type: 'uint256' }]
        }, {
            name: 'transfer',
            type: 'function',
            stateMutability: 'nonpayable',
            inputs: [{ name: 'to', type: 'address' }, { name: 'amount', type: 'uint256' }],
            outputs: [{ name: '', type: 'bool' }]
        }] as const;

        console.log(`[SmartAccount] Checking Gas Funds (Required: ${requiredAmount})...`);

        // 1. Check Smart Account Balance
        const saBalance = await this.publicClient.readContract({
            address: USDC_ADDRESS,
            abi: ERC20_ABI,
            functionName: 'balanceOf',
            args: [this.account.address]
        });

        console.log(`[SmartAccount] Current Balance: ${saBalance}`);

        if (saBalance >= requiredAmount) {
            console.log(`[SmartAccount] ✅ Sufficient funds.`);
            return;
        }

        const shortage = requiredAmount - saBalance;
        console.log(`[SmartAccount] ⚠️ Insufficient funds. Shortage: ${shortage}`);

        // 2. Check EOA Balance
        const eoaAddress = this.signer.account.address;
        const eoaBalance = await this.publicClient.readContract({
            address: USDC_ADDRESS,
            abi: ERC20_ABI,
            functionName: 'balanceOf',
            args: [eoaAddress]
        });

        console.log(`[SmartAccount] EOA Balance: ${eoaBalance}`);

        if (eoaBalance < shortage) {
            throw new Error(`Insufficient funds in both Smart Account (${saBalance}) and EOA (${eoaBalance}). Required: ${requiredAmount}`);
        }

        // 3. Deposit from EOA
        console.log(`[SmartAccount] 🔄 Auto-depositing ${shortage} USDC from EOA...`);

        const hash = await this.signer.writeContract({
            address: USDC_ADDRESS,
            abi: ERC20_ABI,
            functionName: 'transfer',
            args: [this.account.address, shortage],
            chain: this.signer.chain,
            account: this.signer.account
        });

        console.log(`[SmartAccount] Deposit Tx Sent: ${hash}. Waiting for confirmation...`);

        await this.publicClient.waitForTransactionReceipt({ hash });

        console.log(`[SmartAccount] ✅ Deposit confirmed. Proceeding with UserOp.`);
    }
}
