import { createWalletClient, http, toHex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { base } from "viem/chains";
import { config } from "dotenv";
import path from "path";

// Load .env from apps/paymaster
config({ path: path.resolve(__dirname, ".env") });

const PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}`;
const REGISTER_URL = "https://paymaster.a10m.work/v1/register";

if (!PRIVATE_KEY) {
  throw new Error("PRIVATE_KEY environment variable is required");
}

async function main() {
  const account = privateKeyToAccount(PRIVATE_KEY);
  const did = `did:pkh:eip155:8453:${account.address}`;
  const timestamp = Date.now();

  console.log(`Registering DID: ${did}`);

  // Message format from register.ts: `Register A2A Paymaster for ${did} at ${timestamp}`
  const message = `Register A2A Paymaster for ${did} at ${timestamp}`;

  console.log(`Signing message: "${message}"`);

  const signature = await account.signMessage({
    message,
  });

  console.log(`Signature: ${signature}`);

  try {
    const response = await fetch(REGISTER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        did,
        signature,
        timestamp,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Registration failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    console.log("\n✅ Registration Successful!");
    console.log("---------------------------------------------------");
    console.log(`API Key: ${data.apiKey}`);
    console.log("---------------------------------------------------");
    console.log("Please update your .env file with this API Key.");
  } catch (error) {
    console.error("Registration Error:", error);
  }
}

main().catch(console.error);
