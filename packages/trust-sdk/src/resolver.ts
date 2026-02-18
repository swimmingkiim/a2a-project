import { Resolver } from 'did-resolver'
import { getResolver as getKeyResolver } from 'key-did-resolver'
import { getResolver as getEthrResolver } from 'ethr-did-resolver'

export interface ResolverOptions {
    /** Ethereum network name for did:ethr (default: 'base') */
    ethNetwork?: string
    /** RPC URL for did:ethr resolution */
    rpcUrl?: string
}

/**
 * Creates a stateless DID Resolver.
 * No database, no state — only blockchain/key-based resolution.
 */
export function createResolver(options?: ResolverOptions): Resolver {
    const ethNetwork = options?.ethNetwork || 'base'
    const rpcUrl = options?.rpcUrl || 'https://mainnet.base.org'

    return new Resolver({
        ...getKeyResolver(),
        ...getEthrResolver({
            networks: [{ name: ethNetwork, rpcUrl }],
        }),
    })
}
