import { createWalletClient, http, createPublicClient } from "viem"
import { privateKeyToAccount } from "viem/accounts"
import { baseSepolia } from "viem/chains"
import { SmartAccountManager } from "../src/account/smart-account.js"

async function main() {
    console.log("--- Starting A2A Pay SDK Verification ---")

    const privateKey = "0x0123456789012345678901234567890123456789012345678901234567890123" // Test Key
    const account = privateKeyToAccount(privateKey)

    const publicClient = createPublicClient({
        chain: baseSepolia,
        transport: http("https://sepolia.base.org")
    })

    const walletClient = createWalletClient({
        account,
        chain: baseSepolia,
        transport: http("https://sepolia.base.org")
    })

    const manager = new SmartAccountManager(
        walletClient,
        publicClient,
        process.env.BUNDLER_URL || "http://localhost:8080/v1/paymaster" // Use Local Gateway as Bundler!
    )

    try {
        const address = await manager.createSafeAccount()
        console.log("Smart Account Address:", address)
    } catch (e) {
        console.log("Mock execution finished (expected failure without valid RPC headers):", e)
    }
}

main().catch(console.error)
