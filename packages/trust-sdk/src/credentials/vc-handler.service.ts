import { initAgent, Agent } from '../agent'
import { VerifiableCredential } from '@veramo/core'

export class VCHandler {
    private agent?: Agent

    constructor(agent?: Agent) {
        this.agent = agent
    }

    private async getAgent(): Promise<Agent> {
        if (this.agent) return this.agent
        return await initAgent()
    }

    async createCredential(
        issuerDid: string,
        subjectDid: string,
        claims: Record<string, any>
    ): Promise<VerifiableCredential> {
        const agent = await this.getAgent()

        const credential = await agent.createVerifiableCredential({
            credential: {
                issuer: { id: issuerDid },
                credentialSubject: {
                    id: subjectDid,
                    ...claims
                }
            },
            proofFormat: 'jwt',
            save: true
        })

        return credential
    }

    async verifyCredential(vcJwt: string): Promise<boolean> {
        const agent = await this.getAgent()
        const result = await agent.verifyCredential({
            credential: vcJwt
        })

        if (!result.verified) {
            console.error('Credential verification failed:', result.error)
            return false
        }

        // Explicit expiration check
        if (result.verifiableCredential && result.verifiableCredential.expirationDate) {
            const expirationDate = new Date(result.verifiableCredential.expirationDate)
            if (expirationDate < new Date()) {
                console.error(`Credential expired on ${expirationDate.toISOString()}`)
                return false
            }
        }

        return result.verified
    }
}
