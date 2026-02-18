import { privateKeyToAccount } from './node_modules/viem/_esm/accounts/index.js'; // Try direct path or just 'viem' if node resolution works
// Actually, let's try standard import first, if it fails I'll try to find the path.
import { privateKeyToAccount } from 'viem/accounts';
import fs from 'fs';

try {
    const key = fs.readFileSync('.temp_key', 'utf8').trim();
    const account = privateKeyToAccount(key);
    console.log('ADDRESS:' + account.address);
} catch (e) {
    console.error(e);
}
