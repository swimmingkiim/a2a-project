import { initAgent } from '../agent'

export class IdentityManager {
    async createEphemeralDID() {
        const agent = await initAgent()
        const identifier = await agent.didManagerCreate({
            provider: 'did:key'
        })
        return identifier
    }

    async createPersistentDID(alias?: string) {
        const agent = await initAgent()
        const identifier = await agent.didManagerCreate({
            provider: 'did:ethr',
            alias
        })
        return identifier
    }

    async resolveDID(did: string) {
        const agent = await initAgent()
        return await agent.resolveDid({ didUrl: did })
    }
}
