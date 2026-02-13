import { IdentityManager } from '../src/identity/did-manager'
import { VCHandler } from '../src/credentials/vc-handler'

async function main() {
    console.log('--- Starting A2A Trust SDK Verification ---')

    const idManager = new IdentityManager()
    const vcHandler = new VCHandler()

    // 1. Create Issuer DID
    console.log('Creating Issuer DID (did:key)...')
    const issuer = await idManager.createEphemeralDID()
    console.log('Issuer DID:', issuer.did)

    // 2. Create Subject DID
    console.log('Creating Subject DID (did:key)...')
    const subject = await idManager.createEphemeralDID()
    console.log('Subject DID:', subject.did)

    // 3. Issue Credential
    console.log('Issuing VC...')
    const claim = { name: 'A2A Test Agent', role: 'Tester' }
    const vc = await vcHandler.createCredential(issuer.did, subject.did, claim)
    console.log('VC Issued:', vc.proof)

    // 4. Verify Credential
    // Note: createVerifiableCredential returns the object. If proofFormat is jwt, proof field might contain the JWT or we need to request it differently.
    // In Veramo, creating a VC with jwt proof returns a VerifiableCredential object which might have the jwt in `.proof.jwt` or just returned as string if using specific plugins.
    // Let's check Veramo docs behavior: agent.createVerifiableCredential returns VerifiableCredential.
    // However, verifyCredential expects a JWT string or object.

    // For simplicity in this test, we assume standard behavior.

    console.log('Verifying VC...')
    // Cast to any to access internal property if needed, or use proper verification
    // Actually Veramo's `verifyCredential` accepts the object too.
    const isValid = await agent.verifyCredential({ credential: vc })
    console.log('VC Verified:', isValid.verified)
}

// We need to import agent to verify directly in main if we want, or use the handler.
import { agent } from '../src/agent'

main().catch(console.error).then(() => process.exit(0))
