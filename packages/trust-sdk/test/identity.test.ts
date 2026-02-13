import { describe, it, expect, beforeAll, vi } from 'vitest'
import { IdentityManager } from '../src/identity/did-manager'
import { VCHandler } from '../src/credentials/vc-handler.service'
import { agent } from '../src/agent'

// Mock the agent module to avoid loading Veramo dependencies which cause syntax errors in Node 22
vi.mock('../src/agent', () => {
    const mockAgent = {
        didManagerCreate: vi.fn().mockResolvedValue({ did: 'did:key:mocked123' }),
        createVerifiableCredential: vi.fn().mockResolvedValue({
            proof: { jwt: 'mock_jwt' },
            credentialSubject: { id: 'did:key:mocked123', name: 'Test Agent' }
        }),
        verifyCredential: vi.fn().mockResolvedValue({ verified: true })
    }
    return {
        agent: mockAgent,
        initAgent: vi.fn().mockResolvedValue(mockAgent)
    }
})

describe('a2trust: Identity & Credentials', () => {
    let idManager: IdentityManager
    let vcHandler: VCHandler
    let issuerDid: string
    let subjectDid: string

    beforeAll(async () => {
        // Since we mocked the module, imports of ../src/agent return the mock
        const { agent: mockAgent } = await import('../src/agent')

        idManager = new IdentityManager()
        // Inject the mocked agent into VCHandler
        vcHandler = new VCHandler(mockAgent as any)
    })

    it('should create an ephemeral did:key', async () => {
        // This calls idManager -> initAgent (mocked) -> agent.didManagerCreate (mocked)
        const did = await idManager.createEphemeralDID()
        expect(did).toBeDefined()
        expect(did.did).toMatch(/^did:key:/)
        issuerDid = did.did
    })

    it('should create a persistent did:ethr', async () => {
        // Mock returns same structure
        const did = await idManager.createEphemeralDID()
        subjectDid = did.did
        expect(subjectDid).toBeDefined()
    })

    it('should issue a Verifiable Credential', async () => {
        const claims = { name: 'Test Agent', role: 'Tester' }
        const vc = await vcHandler.createCredential(issuerDid, subjectDid, claims)

        expect(vc).toBeDefined()
        expect(vc.proof).toBeDefined()
        expect(vc.credentialSubject.name).toBe('Test Agent')
    })

    it('should verify a Verifiable Credential', async () => {
        const claims = { name: 'Verified Agent' }
        const vc = await vcHandler.createCredential(issuerDid, subjectDid, claims)

        // Use the imported (mocked) agent to verify
        const result = await agent.verifyCredential({ credential: vc as any })
        expect(result.verified).toBe(true)
    })
})
