import crypto from 'crypto'
import { createResolver } from '../resolver'
import { Resolver } from 'did-resolver'

export interface EphemeralIdentity {
    did: string
    keyPair: {
        publicKey: Uint8Array
        secretKey: Uint8Array
    }
}

// Ed25519 multicodec prefix (0xed01)
const ED25519_MULTICODEC_PREFIX = new Uint8Array([0xed, 0x01])

// Base58btc alphabet (Bitcoin alphabet)
const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

/**
 * Encodes a Uint8Array to base58btc string.
 * Pure implementation with no external dependencies.
 */
function base58btcEncode(bytes: Uint8Array): string {
    // Count leading zeros
    let leadingZeros = 0
    for (let i = 0; i < bytes.length && bytes[i] === 0; i++) {
        leadingZeros++
    }

    // Convert to BigInt for base conversion
    let num = BigInt('0x' + Buffer.from(bytes).toString('hex'))
    const chars: string[] = []

    while (num > 0n) {
        const remainder = Number(num % 58n)
        chars.unshift(BASE58_ALPHABET[remainder])
        num = num / 58n
    }

    // Add '1' for each leading zero byte
    for (let i = 0; i < leadingZeros; i++) {
        chars.unshift('1')
    }

    return chars.join('')
}

/**
 * Encodes an Ed25519 public key as a did:key identifier.
 * Format: did:key:z + base58btc(multicodec_prefix + public_key)
 */
function publicKeyToDidKey(publicKey: Uint8Array): string {
    const multicodecKey = new Uint8Array(ED25519_MULTICODEC_PREFIX.length + publicKey.length)
    multicodecKey.set(ED25519_MULTICODEC_PREFIX)
    multicodecKey.set(publicKey, ED25519_MULTICODEC_PREFIX.length)
    return `did:key:z${base58btcEncode(multicodecKey)}`
}

export class IdentityManager {
    private resolver: Resolver

    constructor(resolver?: Resolver) {
        this.resolver = resolver ?? createResolver()
    }

    /**
     * Creates an ephemeral (in-memory) did:key identity.
     * Uses Node.js built-in crypto — no external dependencies, no database.
     */
    async createEphemeralDID(): Promise<EphemeralIdentity> {
        const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519')

        // Export raw key bytes from DER format
        const pubDer = publicKey.export({ type: 'spki', format: 'der' })
        const privDer = privateKey.export({ type: 'pkcs8', format: 'der' })

        // Ed25519 SPKI DER: 12-byte header + 32-byte key
        const rawPublicKey = new Uint8Array(pubDer.subarray(pubDer.length - 32))
        // Ed25519 PKCS8 DER: 16-byte header + 32-byte key
        const rawSecretKey = new Uint8Array(privDer.subarray(privDer.length - 32))

        const did = publicKeyToDidKey(rawPublicKey)

        return {
            did,
            keyPair: { publicKey: rawPublicKey, secretKey: rawSecretKey },
        }
    }

    /**
     * Resolves a DID to its DID Document.
     * Stateless: uses blockchain (did:ethr) or derivation (did:key).
     */
    async resolveDID(did: string): Promise<any> {
        return await this.resolver.resolve(did)
    }

    /**
     * Imports an existing Ed25519 secret key and derives the DID.
     * Use this when you already have a fixed key (e.g., from did_keys.json).
     *
     * @param secretKey - 32-byte Ed25519 secret key as hex string or Uint8Array
     * @returns EphemeralIdentity with the derived DID and key pair
     */
    async fromSecretKey(secretKey: string | Uint8Array): Promise<EphemeralIdentity> {
        const rawSecretKey = typeof secretKey === 'string'
            ? new Uint8Array(Buffer.from(secretKey.replace(/^0x/, ''), 'hex'))
            : secretKey

        if (rawSecretKey.length !== 32) {
            throw new Error(`Invalid Ed25519 secret key length: expected 32 bytes, got ${rawSecretKey.length}`)
        }

        // Reconstruct Node.js KeyObject from raw bytes
        // Ed25519 PKCS8 DER = fixed 16-byte header + 32-byte raw key
        const pkcs8Header = Buffer.from([
            0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06,
            0x03, 0x2b, 0x65, 0x70, 0x04, 0x22, 0x04, 0x20,
        ])
        const pkcs8Der = Buffer.concat([pkcs8Header, Buffer.from(rawSecretKey)])
        const privateKeyObject = crypto.createPrivateKey({
            key: pkcs8Der,
            format: 'der',
            type: 'pkcs8',
        })

        // Derive public key
        const publicKeyObject = crypto.createPublicKey(privateKeyObject)
        const pubDer = publicKeyObject.export({ type: 'spki', format: 'der' })
        const rawPublicKey = new Uint8Array(pubDer.subarray(pubDer.length - 32))

        const did = publicKeyToDidKey(rawPublicKey)

        return {
            did,
            keyPair: { publicKey: rawPublicKey, secretKey: rawSecretKey },
        }
    }
}
