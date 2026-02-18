import { createVerifiableCredentialJwt, verifyCredential as verifyVC } from 'did-jwt-vc'
import { EdDSASigner } from 'did-jwt'
import { Resolver } from 'did-resolver'
import { createResolver } from '../resolver'
import type { EphemeralIdentity } from '../identity/did-manager'

export class VCHandler {
    private resolver: Resolver

    constructor(resolver?: Resolver) {
        this.resolver = resolver ?? createResolver()
    }

    /**
     * Creates a Verifiable Credential as a JWT string.
     * Stateless: signs in-memory, no DB storage.
     *
     * @param issuerDid - DID of the issuer
     * @param subjectDid - DID of the subject
     * @param claims - Claims to include in the credential
     * @param keyPair - Signing key pair (from IdentityManager.createEphemeralDID())
     * @returns JWT string
     */
    async createCredential(
        issuerDid: string,
        subjectDid: string,
        claims: Record<string, any>,
        keyPair?: EphemeralIdentity['keyPair']
    ): Promise<string> {
        if (!keyPair) {
            throw new Error('keyPair is required for credential issuance. Use IdentityManager.createEphemeralDID() to generate one.')
        }

        const signer = EdDSASigner(keyPair.secretKey)

        const vcPayload = {
            sub: subjectDid,
            nbf: Math.floor(Date.now() / 1000),
            vc: {
                '@context': ['https://www.w3.org/2018/credentials/v1'],
                type: ['VerifiableCredential'],
                credentialSubject: {
                    id: subjectDid,
                    ...claims,
                },
            },
        }

        const issuer = {
            did: issuerDid,
            signer,
            alg: 'EdDSA' as const,
        }

        return await createVerifiableCredentialJwt(vcPayload, issuer)
    }

    /**
     * Verifies a Verifiable Credential JWT.
     * Stateless: resolves issuer DID via blockchain/derivation/web,
     * then verifies the JWT signature. No DB required.
     */
    async verifyCredential(vcJwt: string): Promise<boolean> {
        try {
            const result = await verifyVC(vcJwt, this.resolver)

            if (!result.verified) {
                console.error('Credential verification failed:', result)
                return false
            }

            // Explicit expiration check
            if (result.verifiableCredential?.expirationDate) {
                const expirationDate = new Date(result.verifiableCredential.expirationDate)
                if (expirationDate < new Date()) {
                    console.error(`Credential expired on ${expirationDate.toISOString()}`)
                    return false
                }
            }

            return true
        } catch (error) {
            console.error('VC verification error:', error)
            return false
        }
    }
}
