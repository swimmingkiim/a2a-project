import { describe, it, expect } from 'vitest'

/**
 * Stateless Property Tests
 *
 * These tests verify that trust-sdk operates without ANY database dependency.
 * No environment variables, no DB connections, no external state.
 */
describe('trust-sdk: Stateless Properties', () => {
    it('should create an IdentityManager without any env vars or DB', async () => {
        // Must import without AGENT_SECRET_KEY or DB env vars set
        const { IdentityManager } = await import('../src/identity/did-manager')
        const idManager = new IdentityManager()
        expect(idManager).toBeDefined()
    })

    it('should create a VCHandler without any env vars or DB', async () => {
        const { VCHandler } = await import('../src/credentials/vc-handler.service')
        const vcHandler = new VCHandler()
        expect(vcHandler).toBeDefined()
    })

    it('should create a DID without any database', async () => {
        const { IdentityManager } = await import('../src/identity/did-manager')
        const idManager = new IdentityManager()

        const result = await idManager.createEphemeralDID()
        expect(result).toBeDefined()
        expect(result.did).toMatch(/^did:key:/)
        // Must return a key pair (or at least the DID string)
        expect(typeof result.did).toBe('string')
    })

    it('should resolve a did:key without any database', async () => {
        const { IdentityManager } = await import('../src/identity/did-manager')
        const idManager = new IdentityManager()

        const created = await idManager.createEphemeralDID()
        const resolved = await idManager.resolveDID(created.did)

        expect(resolved).toBeDefined()
        expect(resolved.didDocument).toBeDefined()
        expect(resolved.didDocument?.id).toBe(created.did)
    })

    it('should issue and verify a VC E2E without any database', async () => {
        const { IdentityManager } = await import('../src/identity/did-manager')
        const { VCHandler } = await import('../src/credentials/vc-handler.service')

        const idManager = new IdentityManager()
        const vcHandler = new VCHandler()

        // Create a DID
        const identity = await idManager.createEphemeralDID()

        // Issue a self-signed VC
        const vc = await vcHandler.createCredential(
            identity.did,
            identity.did,
            { walletAddress: '0x1234567890abcdef' },
            identity.keyPair // pass the signing key
        )

        expect(vc).toBeDefined()
        expect(typeof vc).toBe('string') // JWT string

        // Verify the VC
        const isValid = await vcHandler.verifyCredential(vc)
        expect(isValid).toBe(true)
    })

    it('should export createResolver from the SDK', async () => {
        const sdk = await import('../src/index')
        expect(sdk.createResolver).toBeDefined()
        expect(typeof sdk.createResolver).toBe('function')
    })

    it('should NOT export agent or initAgent', async () => {
        const sdk = await import('../src/index')
        expect((sdk as any).agent).toBeUndefined()
        expect((sdk as any).initAgent).toBeUndefined()
    })
})
