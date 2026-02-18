import { createPublicClient, http, isAddress, getAddress } from 'viem'
import type { PublicClient, Address, Chain, Transport } from 'viem'
import { z } from 'zod'

// --- ABI Fragment (read-only functions from AgentRegistry.sol) ---
const AGENT_REGISTRY_ABI = [
    {
        type: 'function',
        name: 'agents',
        stateMutability: 'view',
        inputs: [{ name: '', type: 'address' }],
        outputs: [
            { name: 'metadataUrl', type: 'string' },
            { name: 'stakedAmount', type: 'uint256' },
            { name: 'resourceUnits', type: 'uint256' },
            { name: 'registeredAt', type: 'uint64' },
            { name: 'isRegistered', type: 'bool' },
            { name: 'reputation', type: 'uint8' },
            { name: 'lastComplexityHash', type: 'uint256' }
        ]
    },
    {
        type: 'function',
        name: 'getEligibleCandidates',
        stateMutability: 'view',
        inputs: [
            { name: 'minReputation', type: 'uint256' },
            { name: 'minTenure', type: 'uint256' }
        ],
        outputs: [{ name: '', type: 'address[]' }]
    }
] as const

// --- Validation Schemas ---
const EthAddressSchema = z.string().refine(
    (val) => isAddress(val),
    { message: 'Invalid Ethereum address format' }
)

const PaginationSchema = z.object({
    offset: z.number().int().min(0, 'offset must be >= 0').default(0),
    limit: z.number().int().min(1, 'limit must be >= 1').default(10)
}).default({})

// --- Types ---
export interface AgentInfo {
    address: string
    metadataUrl: string
    stakedAmount: bigint
    resourceUnits: bigint
    registeredAt: bigint
    isRegistered: boolean
    reputation: number
    lastComplexityHash: bigint
}

export interface PaginationOptions {
    offset?: number
    limit?: number
}

export interface PaginatedAgents {
    agents: AgentInfo[]
    total: number
    offset: number
    limit: number
}

// --- Constants ---
const MAX_LIMIT = 100

/**
 * Read-only client for querying the on-chain AgentRegistry contract.
 * Does not require a wallet or private key — only an RPC endpoint.
 */
export class RegistryReader {
    private readonly client: PublicClient<Transport, Chain | undefined>
    private readonly registryAddress: Address

    constructor(rpcUrl: string, registryAddress: string) {
        EthAddressSchema.parse(registryAddress)

        this.client = createPublicClient({
            transport: http(rpcUrl)
        })
        this.registryAddress = getAddress(registryAddress)
    }

    /**
     * Returns a paginated list of registered agents.
     * Uses `getEligibleCandidates(0, 0)` to fetch all addresses,
     * then applies client-side offset/limit slicing.
     */
    async getRegisteredAgents(options?: PaginationOptions): Promise<PaginatedAgents> {
        const { offset, limit: rawLimit } = PaginationSchema.parse(options)
        const limit = Math.min(rawLimit, MAX_LIMIT)

        const allAddresses = await this.client.readContract({
            address: this.registryAddress,
            abi: AGENT_REGISTRY_ABI,
            functionName: 'getEligibleCandidates',
            args: [0n, 0n]
        }) as readonly string[]

        const total = allAddresses.length
        const sliced = allAddresses.slice(offset, offset + limit)

        const agents = await Promise.all(
            sliced.map((addr) => this.fetchAgentData(addr as Address))
        )

        return { agents, total, offset, limit }
    }

    /**
     * Returns detailed info for a specific agent.
     */
    async getAgentInfo(address: string): Promise<AgentInfo> {
        const validated = EthAddressSchema.parse(address)
        return this.fetchAgentData(getAddress(validated))
    }

    /**
     * Checks if an address is currently registered as an agent.
     */
    async isAgentRegistered(address: string): Promise<boolean> {
        const info = await this.getAgentInfo(address)
        return info.isRegistered
    }

    /**
     * Internal: fetches raw agent struct from the contract and maps to AgentInfo.
     */
    private async fetchAgentData(address: Address): Promise<AgentInfo> {
        const raw = await this.client.readContract({
            address: this.registryAddress,
            abi: AGENT_REGISTRY_ABI,
            functionName: 'agents',
            args: [address]
        }) as readonly [string, bigint, bigint, bigint, boolean, number, bigint]

        return {
            address,
            metadataUrl: raw[0],
            stakedAmount: raw[1],
            resourceUnits: raw[2],
            registeredAt: raw[3],
            isRegistered: raw[4],
            reputation: raw[5],
            lastComplexityHash: raw[6]
        }
    }
}
