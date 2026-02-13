
import { createPublicClient, http } from 'viem';
import { base } from 'viem/chains';

const PAYMASTER_URL = 'https://paymaster.a10m.work/v1/paymaster';
const API_KEY = process.env.A2A_PAYMASTER_API_KEY;

async function main() {
    console.log('🏥 Paymaster Service Health Check');
    console.log('='.repeat(40));
    console.log(`URL: ${PAYMASTER_URL}`);

    if (!API_KEY) {
        console.warn('⚠️  A2A_PAYMASTER_API_KEY not set. Auth tests may fail.');
    }

    // 1. Health Check (GET /health)
    console.log('\n1. Checking /health endpoint...');
    try {
        const healthRes = await fetch('https://paymaster.a10m.work/health');
        console.log(`   Status: ${healthRes.status} ${healthRes.statusText}`);
        if (healthRes.ok) {
            console.log('   ✅ Health check passed');
        } else {
            console.error('   ❌ Health check failed');
        }
    } catch (e) {
        console.error('   ❌ Connection failed:', e);
    }

    // 2. Auth Check (Invalid Key)
    console.log('\n2. Testing Invalid API Key...');
    try {
        const badRes = await fetch(PAYMASTER_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'x-api-key': 'invalid-key' },
            body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'eth_chainId', params: [] })
        });
        console.log(`   Status: ${badRes.status} ${badRes.statusText}`);
        if (badRes.status === 401) {
            console.log('   ✅ Correctly rejected invalid key');
        } else {
            console.warn(`   ⚠️  Unexpected status: ${badRes.status}`);
        }
    } catch (e) {
        console.error('   ❌ Auth test failed:', e);
    }

    // 3. Chain ID Check (Valid Key)
    console.log('\n3. Testing Valid API Key (eth_chainId)...');
    try {
        const res = await fetch(PAYMASTER_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'x-api-key': API_KEY || '' },
            body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'eth_chainId', params: [] })
        });

        if (res.ok) {
            const data = await res.json();
            console.log('   Response:', JSON.stringify(data));
            if (data.result === '0x2105' || data.result === '8453') { // Base Mainnet Chain ID
                console.log('   ✅ Chain ID matched (Base Mainnet)');
            } else {
                console.log(`   ℹ️  Chain ID: ${data.result}`);
            }
        } else {
            console.error(`   ❌ Request failed: ${res.status}`);
            const text = await res.text();
            console.error('   Body:', text);
        }
    } catch (e) {
        console.error('   ❌ Chain ID test failed:', e);
    }

    console.log('\n' + '='.repeat(40));
}

main().catch(console.error);
