import {
    keccak256,
    toHex,
    encodeAbiParameters,
    isAddress,
} from 'viem'
import { privateKeyToAccount } from 'viem/accounts'
import type { Account } from 'viem'
import { z } from 'zod'

// --- Validation ---
const EthAddressSchema = z.string().refine(
    (val) => isAddress(val),
    { message: 'Invalid Ethereum address format' }
)

// --- EIP-712 Type Definitions (must match CredentialVerifier.sol) ---
const EIP712_DOMAIN = {
    name: 'CredentialVerifier',
    version: '1',
} as const

const ATTESTATION_TYPES = {
    Attestation: [
        { name: 'user', type: 'address' },
        { name: 'didHash', type: 'bytes32' },
        { name: 'deadline', type: 'uint256' },
    ],
} as const

// --- Types ---

/**
 * Function signature for VC verification.
 * Injected by the caller — can be trust-sdk's VCHandler or any custom impl.
 */
export type VerifyVCFunction = (vcJwt: string) => Promise<{ valid: boolean; did: string }>

export interface AttestationSignerOptions {
    /** Hex-encoded secp256k1 private key of the trusted signer */
    privateKey: `0x${string}`
    /** Address of the deployed CredentialVerifier contract */
    verifierContractAddress: string
    /** Chain ID (e.g., 8453 for Base Mainnet) */
    chainId: number
    /** Injected VC verification function */
    verifyVC: VerifyVCFunction
    /** Attestation validity duration in seconds (default: 3600 = 1 hour) */
    ttlSeconds?: number
}

/**
 * Structured attestation proof ready for on-chain submission.
 */
export interface AttestationProof {
    /** keccak256 hash of the verified DID */
    didHash: `0x${string}`
    /** Unix timestamp after which the attestation expires */
    deadline: bigint
    /** EIP-712 ECDSA signature */
    signature: string
    /** Encodes the proof as ABI-packed bytes for contract submission */
    encode: () => `0x${string}`
}

const DEFAULT_TTL_SECONDS = 3600 // 1 hour

/**
 * Creates EIP-712 signed attestation proofs for the on-chain CredentialVerifier.
 *
 * Architecture:
 *   1. Verifies VC JWT using the injected verifyVC function
 *   2. Extracts the DID and hashes it (nullifier)
 *   3. Signs an EIP-712 typed data struct with the trusted signer key
 *   4. Returns encoded proof ready for AgentRegistry.register()
 *
 * @example
 * ```ts
 * import { AttestationSigner } from '@swimmingkiim/api-sdk'
 * import { VCHandler } from '@swimmingkiim/trust-sdk'
 *
 * const vcHandler = new VCHandler()
 * const signer = new AttestationSigner({
 *     privateKey: process.env.SIGNER_KEY as `0x${string}`,
 *     verifierContractAddress: '0x...',
 *     chainId: 8453,
 *     verifyVC: async (jwt) => {
 *         const valid = await vcHandler.verifyCredential(jwt)
 *         // Extract DID from JWT payload
 *         const payload = JSON.parse(atob(jwt.split('.')[1]))
 *         return { valid, did: payload.iss }
 *     },
 * })
 *
 * const proof = await signer.createAttestation(vcJwt, walletAddress)
 * // proof.encode() → bytes for AgentRegistry.register(meta, units, proof.encode())
 * ```
 */
export class AttestationSigner {
    private readonly account: Account
    private readonly verifierContractAddress: `0x${string}`
    private readonly chainId: number
    private readonly verifyVC: VerifyVCFunction
    private readonly ttlSeconds: number

    constructor(options: AttestationSignerOptions) {
        EthAddressSchema.parse(options.verifierContractAddress)

        this.account = privateKeyToAccount(options.privateKey)
        this.verifierContractAddress = options.verifierContractAddress as `0x${string}`
        this.chainId = options.chainId
        this.verifyVC = options.verifyVC
        this.ttlSeconds = options.ttlSeconds ?? DEFAULT_TTL_SECONDS
    }

    /**
     * Verifies a VC JWT and produces a signed attestation proof.
     *
     * @param vcJwt - Verifiable Credential JWT string
     * @param walletAddress - The Ethereum address of the agent being attested
     * @returns AttestationProof with didHash, deadline, signature, and encode()
     */
    async createAttestation(vcJwt: string, walletAddress: string): Promise<AttestationProof> {
        // 1. Validate wallet address
        EthAddressSchema.parse(walletAddress)

        // 2. Verify VC
        const { valid, did } = await this.verifyVC(vcJwt)
        if (!valid) {
            throw new Error('VC verification failed')
        }

        // 3. Hash the DID for nullifier
        const didHash = keccak256(toHex(did)) as `0x${string}`

        // 4. Calculate deadline
        const deadline = BigInt(Math.floor(Date.now() / 1000) + this.ttlSeconds)

        // 5. Sign EIP-712 typed data
        const signature = await this.account.signTypedData({
            domain: {
                ...EIP712_DOMAIN,
                chainId: this.chainId,
                verifyingContract: this.verifierContractAddress,
            },
            types: ATTESTATION_TYPES,
            primaryType: 'Attestation',
            message: {
                user: walletAddress as `0x${string}`,
                didHash,
                deadline,
            },
        })

        // 6. Return structured proof
        return {
            didHash,
            deadline,
            signature,
            encode: () => encodeAbiParameters(
                [
                    { name: 'didHash', type: 'bytes32' },
                    { name: 'deadline', type: 'uint256' },
                    { name: 'signature', type: 'bytes' },
                ],
                [didHash, deadline, signature as `0x${string}`]
            ),
        }
    }
}
