import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("CredentialVerifier", function () {
    let verifier: any;
    let admin: SignerWithAddress;
    let trustedSigner: SignerWithAddress;
    let user: SignerWithAddress;
    let attacker: SignerWithAddress;

    // EIP-712 domain and type definitions
    const ATTESTATION_TYPEHASH = "Attestation(address user,bytes32 didHash,uint256 deadline)";

    let domain: {
        name: string;
        version: string;
        chainId: number;
        verifyingContract: string;
    };

    const types = {
        Attestation: [
            { name: "user", type: "address" },
            { name: "didHash", type: "bytes32" },
            { name: "deadline", type: "uint256" },
        ],
    };

    /**
     * Helper: creates an EIP-712 signed attestation proof.
     */
    async function createAttestation(
        signer: SignerWithAddress,
        userAddress: string,
        didHash: string,
        deadline: bigint
    ): Promise<string> {
        const signature = await signer.signTypedData(domain, types, {
            user: userAddress,
            didHash: didHash,
            deadline: deadline,
        });

        // Encode proof: (bytes32 didHash, uint256 deadline, bytes signature)
        const proof = ethers.AbiCoder.defaultAbiCoder().encode(
            ["bytes32", "uint256", "bytes"],
            [didHash, deadline, signature]
        );
        return proof;
    }

    beforeEach(async function () {
        [admin, trustedSigner, user, attacker] = await ethers.getSigners();

        const VerifierFactory = await ethers.getContractFactory("CredentialVerifier");
        verifier = await upgrades.deployProxy(VerifierFactory, [
            admin.address,
            trustedSigner.address,
        ], { kind: "uups" });
        await verifier.waitForDeployment();

        domain = {
            name: "CredentialVerifier",
            version: "1",
            chainId: (await ethers.provider.getNetwork()).chainId as unknown as number,
            verifyingContract: await verifier.getAddress(),
        };
    });

    describe("Valid Attestation", function () {
        it("should accept a valid attestation from trusted signer", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zExampleDID123"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

            const proof = await createAttestation(trustedSigner, user.address, didHash, deadline);

            const result = await verifier.verifyCredential.staticCall(user.address, proof);
            expect(result).to.be.true;
        });

        it("should mark nullifier as used after verification", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zExampleDID456"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            const proof = await createAttestation(trustedSigner, user.address, didHash, deadline);

            // First call: succeeds (mutates state)
            await verifier.verifyCredential(user.address, proof);

            // Nullifier should now be marked as used
            expect(await verifier.usedNullifiers(didHash)).to.be.true;
        });
    });

    describe("Sybil Resistance (Nullifier)", function () {
        it("should reject a second registration with the same DID", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zSybilTest"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            // First registration: succeeds
            const proof1 = await createAttestation(trustedSigner, user.address, didHash, deadline);
            await verifier.verifyCredential(user.address, proof1);

            // Second registration with same DID (different user): should fail
            const proof2 = await createAttestation(trustedSigner, attacker.address, didHash, deadline);
            await expect(
                verifier.verifyCredential(attacker.address, proof2)
            ).to.be.revertedWith("Nullifier already used");
        });
    });

    describe("Deadline Enforcement", function () {
        it("should reject an expired attestation", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zExpiredTest"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) - 3600); // 1 hour ago

            const proof = await createAttestation(trustedSigner, user.address, didHash, deadline);

            await expect(
                verifier.verifyCredential(user.address, proof)
            ).to.be.revertedWith("Attestation expired");
        });
    });

    describe("Signer Validation", function () {
        it("should reject an attestation from an untrusted signer", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zUntrustedSigner"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            // Attacker signs instead of trustedSigner
            const proof = await createAttestation(attacker, user.address, didHash, deadline);

            await expect(
                verifier.verifyCredential(user.address, proof)
            ).to.be.revertedWith("Invalid signer");
        });

        it("should reject an attestation targeting a different user", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zWrongUser"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            // Signed for user.address but submitted for attacker.address
            const proof = await createAttestation(trustedSigner, user.address, didHash, deadline);

            await expect(
                verifier.verifyCredential(attacker.address, proof)
            ).to.be.revertedWith("Invalid signer");
        });
    });

    describe("Signer Rotation", function () {
        it("should allow admin to rotate the trusted signer", async function () {
            const newSigner = attacker; // reuse attacker as new signer for simplicity
            await verifier.connect(admin).setTrustedSigner(newSigner.address);

            expect(await verifier.trustedSigner()).to.equal(newSigner.address);

            // New signer should now be accepted
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zNewSigner"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            const proof = await createAttestation(newSigner, user.address, didHash, deadline);
            const result = await verifier.verifyCredential.staticCall(user.address, proof);
            expect(result).to.be.true;
        });

        it("should reject signer rotation from non-admin", async function () {
            await expect(
                verifier.connect(attacker).setTrustedSigner(attacker.address)
            ).to.be.reverted; // AccessControl revert
        });

        it("should reject setting zero address as signer", async function () {
            await expect(
                verifier.connect(admin).setTrustedSigner(ethers.ZeroAddress)
            ).to.be.revertedWith("Invalid signer address");
        });
    });
});
