import { describe, it, expect, vi, beforeEach } from 'vitest'
import { privateKeyToAccount, generatePrivateKey } from 'viem/accounts'
import { hashTypedData, recoverAddress, decodeAbiParameters } from 'viem'

// We'll import AttestationSigner after creating it
import { AttestationSigner } from '../src/discovery/attestation-signer.js'
import type { AttestationProof } from '../src/discovery/attestation-signer.js'

const TEST_CHAIN_ID = 8453 // Base Mainnet
const TEST_VERIFIER_ADDRESS = '0x1234567890123456789012345678901234567890'
const TEST_WALLET = '0xaabbccddee11223344556677889900aabbccddee'
const TEST_VC_JWT = 'eyJhbGciOiJFZERTQSJ9.eyJzdWIiOiJkaWQ6a2V5Onp0ZXN0In0.c2lnbmF0dXJl'
const TEST_DID = 'did:key:zTestDID123456789'

describe('AttestationSigner', () => {
    let signerKey: `0x${string}`
    let attestationSigner: AttestationSigner

    // Mock VC verifier that always succeeds and returns DID
    const mockVerifyVC = vi.fn<(vcJwt: string) => Promise<{ valid: boolean; did: string }>>()

    beforeEach(() => {
        vi.clearAllMocks()
        signerKey = generatePrivateKey()

        attestationSigner = new AttestationSigner({
            privateKey: signerKey,
            verifierContractAddress: TEST_VERIFIER_ADDRESS,
            chainId: TEST_CHAIN_ID,
            verifyVC: mockVerifyVC,
        })
    })

    describe('createAttestation', () => {
        it('should produce a valid EIP-712 signed proof', async () => {
            mockVerifyVC.mockResolvedValueOnce({ valid: true, did: TEST_DID })

            const proof = await attestationSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)

            // Proof should contain didHash, deadline, and signature
            expect(proof.didHash).toBeDefined()
            expect(proof.deadline).toBeGreaterThan(BigInt(Math.floor(Date.now() / 1000)))
            expect(proof.signature).toBeDefined()
            expect(proof.signature).toMatch(/^0x[0-9a-f]+$/i)
        })

        it('should produce a proof whose signer recovers to the correct address', async () => {
            mockVerifyVC.mockResolvedValueOnce({ valid: true, did: TEST_DID })

            const proof = await attestationSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)
            const signerAccount = privateKeyToAccount(signerKey)

            // Reconstruct EIP-712 digest and recover
            const digest = hashTypedData({
                domain: {
                    name: 'CredentialVerifier',
                    version: '1',
                    chainId: TEST_CHAIN_ID,
                    verifyingContract: TEST_VERIFIER_ADDRESS as `0x${string}`,
                },
                types: {
                    Attestation: [
                        { name: 'user', type: 'address' },
                        { name: 'didHash', type: 'bytes32' },
                        { name: 'deadline', type: 'uint256' },
                    ],
                },
                primaryType: 'Attestation',
                message: {
                    user: TEST_WALLET as `0x${string}`,
                    didHash: proof.didHash,
                    deadline: proof.deadline,
                },
            })

            const recovered = await recoverAddress({
                hash: digest,
                signature: proof.signature as `0x${string}`,
            })

            expect(recovered.toLowerCase()).toBe(signerAccount.address.toLowerCase())
        })

        it('should produce a deterministic didHash from the DID', async () => {
            mockVerifyVC.mockResolvedValueOnce({ valid: true, did: TEST_DID })
            const proof1 = await attestationSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)

            mockVerifyVC.mockResolvedValueOnce({ valid: true, did: TEST_DID })
            const proof2 = await attestationSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)

            // Same DID → same didHash
            expect(proof1.didHash).toBe(proof2.didHash)
        })

        it('should encode proof as ABI-packed bytes', async () => {
            mockVerifyVC.mockResolvedValueOnce({ valid: true, did: TEST_DID })

            const proof = await attestationSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)
            const encoded = proof.encode()

            // Should be decodable
            const [didHash, deadline, signature] = decodeAbiParameters(
                [
                    { name: 'didHash', type: 'bytes32' },
                    { name: 'deadline', type: 'uint256' },
                    { name: 'signature', type: 'bytes' },
                ],
                encoded
            )

            expect(didHash).toBe(proof.didHash)
            expect(deadline).toBe(proof.deadline)
            expect(signature).toBe(proof.signature)
        })
    })

    describe('VC Verification Failure', () => {
        it('should throw if VC verification fails', async () => {
            mockVerifyVC.mockResolvedValueOnce({ valid: false, did: '' })

            await expect(
                attestationSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)
            ).rejects.toThrow('VC verification failed')
        })

        it('should throw if VC verifier throws', async () => {
            mockVerifyVC.mockRejectedValueOnce(new Error('Network error'))

            await expect(
                attestationSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)
            ).rejects.toThrow('Network error')
        })
    })

    describe('Input Validation', () => {
        it('should reject an invalid wallet address', async () => {
            await expect(
                attestationSigner.createAttestation(TEST_VC_JWT, 'not-an-address')
            ).rejects.toThrow()
        })
    })

    describe('Custom TTL', () => {
        it('should respect custom ttlSeconds', async () => {
            const customSigner = new AttestationSigner({
                privateKey: signerKey,
                verifierContractAddress: TEST_VERIFIER_ADDRESS,
                chainId: TEST_CHAIN_ID,
                verifyVC: mockVerifyVC,
                ttlSeconds: 60, // 1 minute
            })

            mockVerifyVC.mockResolvedValueOnce({ valid: true, did: TEST_DID })
            const proof = await customSigner.createAttestation(TEST_VC_JWT, TEST_WALLET)

            const now = BigInt(Math.floor(Date.now() / 1000))
            // Deadline should be within 60-65 seconds from now (some tolerance)
            expect(proof.deadline - now).toBeLessThanOrEqual(65n)
            expect(proof.deadline - now).toBeGreaterThanOrEqual(55n)
        })
    })
})
