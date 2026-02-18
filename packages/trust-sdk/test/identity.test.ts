import { describe, it, expect } from 'vitest'
import { IdentityManager } from '../src/identity/did-manager'
import { VCHandler } from '../src/credentials/vc-handler.service'

/**
 * Identity & Credentials Tests (No Mocks)
 *
 * These test REAL in-memory behavior — no vi.mock, no DB.
 */
describe('a2trust: Identity & Credentials', () => {
    let idManager: IdentityManager
    let vcHandler: VCHandler

    idManager = new IdentityManager()
    vcHandler = new VCHandler()

    it('should create an ephemeral did:key', async () => {
        const result = await idManager.createEphemeralDID()
        expect(result).toBeDefined()
        expect(result.did).toMatch(/^did:key:/)
    })

    it('should resolve a created DID', async () => {
        const created = await idManager.createEphemeralDID()
        const resolved = await idManager.resolveDID(created.did)

        expect(resolved).toBeDefined()
        expect(resolved.didDocument).toBeDefined()
        expect(resolved.didDocument?.id).toBe(created.did)
    })

    it('should issue a Verifiable Credential as JWT', async () => {
        const identity = await idManager.createEphemeralDID()
        const claims = { name: 'Test Agent', role: 'Tester' }

        const vc = await vcHandler.createCredential(
            identity.did,
            identity.did,
            claims,
            identity.keyPair
        )

        expect(vc).toBeDefined()
        expect(typeof vc).toBe('string')

        // Should be a valid JWT (3 parts separated by dots)
        const parts = vc.split('.')
        expect(parts.length).toBe(3)
    })

    it('should verify a valid Verifiable Credential', async () => {
        const identity = await idManager.createEphemeralDID()
        const claims = { name: 'Verified Agent' }

        const vcJwt = await vcHandler.createCredential(
            identity.did,
            identity.did,
            claims,
            identity.keyPair
        )

        const result = await vcHandler.verifyCredential(vcJwt)
        expect(result).toBe(true)
    })

    it('createCredential should include claims in the VC payload', async () => {
        const identity = await idManager.createEphemeralDID()
        const claims = { walletAddress: '0xABCDEF1234567890' }

        const vcJwt = await vcHandler.createCredential(
            identity.did,
            identity.did,
            claims,
            identity.keyPair
        )

        // Decode the JWT payload
        const payload = JSON.parse(Buffer.from(vcJwt.split('.')[1], 'base64').toString())
        expect(payload.vc.credentialSubject.walletAddress).toBe('0xABCDEF1234567890')
    })
})
