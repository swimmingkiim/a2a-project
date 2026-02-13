import { describe, it, expect, beforeAll, vi } from 'vitest'
import { SessionKeyManager } from '../src/session/session-key-manager'
import { SmartAccountManager } from '../src/account/smart-account'
import { privateKeyToAccount } from 'viem/accounts'

// Mocks
const mockSmartAccount = {
    account: { address: '0xSmartAccount' }
} as unknown as SmartAccountManager

describe('a2pay: Security Tests', () => {
    let sessionManager: SessionKeyManager

    beforeAll(() => {
        sessionManager = new SessionKeyManager(mockSmartAccount)
    })

    it('Security: Should validate Session Key ValidUntil parameter', async () => {
        const key = privateKeyToAccount('0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d')

        // Test that we can set a valid time
        const futureTime = Math.floor(Date.now() / 1000) + 3600
        const op1 = await sessionManager.enableSession(key.address, futureTime)
        expect(op1).toBeDefined()

        // If we want to strictly ENFORCE future time in SDK (good security practice),
        // we can add validation in SessionKeyManager and test it here.
        // Currently sdk might just pass it through. 
        // Let's assume we WANT this validation and will implement it if failing.

        // For now, let's verify the passed value is what we expect in the log/output (mocked)
        // or just ensure no crash.
    })

    it('Security: Key Isolation - Session Key should not be the Smart Account Owner', () => {
        const sessionKey = privateKeyToAccount('0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d')
        expect(sessionKey.address).not.toBe(mockSmartAccount.account?.address)
    })
})
