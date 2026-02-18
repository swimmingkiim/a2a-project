import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { AgentInfo, PaginatedAgents } from '../src/discovery/registry-reader.js'

// --- Mock viem ---
const { mockReadContract } = vi.hoisted(() => ({
    mockReadContract: vi.fn()
}))

vi.mock('viem', () => ({
    createPublicClient: vi.fn(() => ({
        readContract: mockReadContract
    })),
    http: vi.fn(() => ({})),
    getAddress: vi.fn((addr: string) => addr),
    isAddress: vi.fn((addr: string) => /^0x[a-fA-F0-9]{40}$/.test(addr))
}))

import { RegistryReader } from '../src/discovery/registry-reader.js'

// --- Test Data ---
const VALID_ADDRESS_A = '0x1111111111111111111111111111111111111111'
const VALID_ADDRESS_B = '0x2222222222222222222222222222222222222222'
const VALID_ADDRESS_C = '0x3333333333333333333333333333333333333333'
const INVALID_ADDRESS = '0xINVALID'
const REGISTRY_ADDRESS = '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
const RPC_URL = 'https://mainnet.base.org'

const MOCK_AGENT_RAW = [
    'https://example.com/metadata.json', // metadataUrl
    1000000000000000000n,                // stakedAmount (1 DAIM)
    5n,                                  // resourceUnits
    BigInt(Math.floor(Date.now() / 1000) - 86400), // registeredAt (24h ago)
    true,                                // isRegistered
    75,                                  // reputation
    0n                                   // lastComplexityHash
] as const

describe('RegistryReader', () => {
    let reader: RegistryReader

    beforeEach(() => {
        vi.clearAllMocks()
        reader = new RegistryReader(RPC_URL, REGISTRY_ADDRESS)
    })

    // ========================================================
    // getRegisteredAgents
    // ========================================================
    describe('getRegisteredAgents', () => {
        it('should return paginated results with default offset=0, limit=10', async () => {
            const addresses = [VALID_ADDRESS_A, VALID_ADDRESS_B, VALID_ADDRESS_C]
            mockReadContract.mockResolvedValueOnce(addresses)

            // Individual agent calls for the sliced range
            for (const _addr of addresses) {
                mockReadContract.mockResolvedValueOnce(MOCK_AGENT_RAW)
            }

            const result: PaginatedAgents = await reader.getRegisteredAgents()

            expect(result.agents).toHaveLength(3)
            expect(result.total).toBe(3)
            expect(result.offset).toBe(0)
            expect(result.limit).toBe(10)
        })

        it('should respect offset and limit parameters', async () => {
            const addresses = [VALID_ADDRESS_A, VALID_ADDRESS_B, VALID_ADDRESS_C]
            mockReadContract.mockResolvedValueOnce(addresses)

            // Only VALID_ADDRESS_B should be fetched (offset=1, limit=1)
            mockReadContract.mockResolvedValueOnce(MOCK_AGENT_RAW)

            const result = await reader.getRegisteredAgents({ offset: 1, limit: 1 })

            expect(result.agents).toHaveLength(1)
            expect(result.agents[0].address).toBe(VALID_ADDRESS_B)
            expect(result.total).toBe(3)
            expect(result.offset).toBe(1)
            expect(result.limit).toBe(1)
        })

        it('should clamp limit to MAX_LIMIT (100)', async () => {
            const addresses = [VALID_ADDRESS_A]
            mockReadContract.mockResolvedValueOnce(addresses)
            mockReadContract.mockResolvedValueOnce(MOCK_AGENT_RAW)

            const result = await reader.getRegisteredAgents({ limit: 500 })

            expect(result.limit).toBe(100)
        })

        it('should return empty array when offset exceeds total', async () => {
            const addresses = [VALID_ADDRESS_A]
            mockReadContract.mockResolvedValueOnce(addresses)

            const result = await reader.getRegisteredAgents({ offset: 10 })

            expect(result.agents).toHaveLength(0)
            expect(result.total).toBe(1)
        })

        it('should reject negative offset', async () => {
            await expect(reader.getRegisteredAgents({ offset: -1 }))
                .rejects.toThrow()
        })

        it('should reject zero or negative limit', async () => {
            await expect(reader.getRegisteredAgents({ limit: 0 }))
                .rejects.toThrow()
            await expect(reader.getRegisteredAgents({ limit: -5 }))
                .rejects.toThrow()
        })
    })

    // ========================================================
    // getAgentInfo
    // ========================================================
    describe('getAgentInfo', () => {
        it('should return agent details for a valid registered address', async () => {
            mockReadContract.mockResolvedValueOnce(MOCK_AGENT_RAW)

            const info: AgentInfo = await reader.getAgentInfo(VALID_ADDRESS_A)

            expect(info.address).toBe(VALID_ADDRESS_A)
            expect(info.metadataUrl).toBe('https://example.com/metadata.json')
            expect(info.stakedAmount).toBe(1000000000000000000n)
            expect(info.resourceUnits).toBe(5n)
            expect(info.isRegistered).toBe(true)
            expect(info.reputation).toBe(75)
        })

        it('should reject an invalid Ethereum address', async () => {
            await expect(reader.getAgentInfo(INVALID_ADDRESS))
                .rejects.toThrow()
        })
    })

    // ========================================================
    // isAgentRegistered
    // ========================================================
    describe('isAgentRegistered', () => {
        it('should return true for a registered agent', async () => {
            mockReadContract.mockResolvedValueOnce(MOCK_AGENT_RAW)

            const result = await reader.isAgentRegistered(VALID_ADDRESS_A)
            expect(result).toBe(true)
        })

        it('should return false for an unregistered agent', async () => {
            const unregisteredRaw = [
                'https://example.com/metadata.json',
                1000000000000000000n,
                5n,
                BigInt(Math.floor(Date.now() / 1000) - 86400),
                false,    // isRegistered = false
                75,
                0n
            ]
            mockReadContract.mockResolvedValueOnce(unregisteredRaw)

            const result = await reader.isAgentRegistered(VALID_ADDRESS_A)
            expect(result).toBe(false)
        })

        it('should reject an invalid Ethereum address', async () => {
            await expect(reader.isAgentRegistered(INVALID_ADDRESS))
                .rejects.toThrow()
        })
    })
})
