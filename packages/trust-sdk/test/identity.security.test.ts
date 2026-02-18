import { describe, it, expect } from 'vitest'
import { IdentityManager } from '../src/identity/did-manager'
import { VCHandler } from '../src/credentials/vc-handler.service'

/**
 * Security Tests (No Mocks — Real JWT Verification)
 */
describe('a2trust: Security Tests', () => {
    let idManager: IdentityManager
    let vcHandler: VCHandler

    idManager = new IdentityManager()
    vcHandler = new VCHandler()

    it('should reject a tampered JWT', async () => {
        const identity = await idManager.createEphemeralDID()

        const validJwt = await vcHandler.createCredential(
            identity.did,
            identity.did,
            { walletAddress: '0x123' },
            identity.keyPair
        )

        // Tamper with the JWT payload
        const parts = validJwt.split('.')
        const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString())
        payload.vc.credentialSubject.walletAddress = '0xHACKED'
        parts[1] = Buffer.from(JSON.stringify(payload)).toString('base64url')
        const tamperedJwt = parts.join('.')

        const result = await vcHandler.verifyCredential(tamperedJwt)
        expect(result).toBe(false)
    })

    it('should reject a completely invalid JWT string', async () => {
        const result = await vcHandler.verifyCredential('not.a.valid.jwt')
        expect(result).toBe(false)
    })

    it('should reject a JWT signed by unknown issuer', async () => {
        // Create a VC signed by identity A
        const identityA = await idManager.createEphemeralDID()
        const identityB = await idManager.createEphemeralDID()

        // Sign with A's key but claim issuer is B
        // This should fail because B's DID document won't match A's key
        const vcJwt = await vcHandler.createCredential(
            identityB.did,  // claim to be B
            identityB.did,
            { walletAddress: '0x123' },
            identityA.keyPair  // but sign with A's key
        )

        const result = await vcHandler.verifyCredential(vcJwt)
        expect(result).toBe(false)
    })
})
