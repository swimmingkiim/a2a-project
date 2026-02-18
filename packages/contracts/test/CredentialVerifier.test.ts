import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("CredentialVerifier (Web of Trust)", function () {
    let verifier: any;
    let registry: any;
    let daimToken: any;
    let mockOracle: any;
    let mockVerifierForBootstrap: any; // Dummy verifier for AgentRegistry's own init

    let admin: SignerWithAddress;
    let bootstrapVoucher: SignerWithAddress;
    let agentA: SignerWithAddress;  // Will be registered, then vouch for agentB
    let agentB: SignerWithAddress;  // New agent to be vouched for
    let attacker: SignerWithAddress;

    const types = {
        Attestation: [
            { name: "user", type: "address" },
            { name: "didHash", type: "bytes32" },
            { name: "deadline", type: "uint256" },
        ],
    };

    let domain: {
        name: string;
        version: string;
        chainId: number;
        verifyingContract: string;
    };

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
        return ethers.AbiCoder.defaultAbiCoder().encode(
            ["bytes32", "uint256", "bytes"],
            [didHash, deadline, signature]
        );
    }

    beforeEach(async function () {
        [admin, bootstrapVoucher, agentA, agentB, attacker] = await ethers.getSigners();

        // 1. Deploy DaimToken
        const TokenFactory = await ethers.getContractFactory("DaimToken");
        daimToken = await upgrades.deployProxy(TokenFactory, [admin.address], { kind: "uups" });
        await daimToken.waitForDeployment();
        const MINTER_ROLE = await daimToken.MINTER_ROLE();
        await daimToken.grantRole(MINTER_ROLE, admin.address);
        await daimToken.mint(agentA.address, ethers.parseEther("100000"));

        // 2. Deploy Mock Oracle ($1.00)
        const OracleFactory = await ethers.getContractFactory("MockV3Aggregator");
        mockOracle = await OracleFactory.deploy(8, ethers.parseUnits("1", 8));
        await mockOracle.waitForDeployment();

        // 3. Deploy a MockVerifier for AgentRegistry's own init (always passes)
        const MockVerifierFactory = await ethers.getContractFactory("contracts/mocks/MockVerifier.sol:MockVerifier");
        mockVerifierForBootstrap = await MockVerifierFactory.deploy();
        await mockVerifierForBootstrap.waitForDeployment();

        // 4. Deploy AgentRegistry
        const RegistryFactory = await ethers.getContractFactory("AgentRegistry");
        registry = await upgrades.deployProxy(RegistryFactory, [
            await daimToken.getAddress(),
            await mockOracle.getAddress(),
            admin.address, // treasury
            await mockVerifierForBootstrap.getAddress(),
            admin.address, // admin
        ], { kind: "uups" });
        await registry.waitForDeployment();

        // Register agentA in the registry (so agentA can vouch for others)
        await daimToken.connect(agentA).approve(await registry.getAddress(), ethers.MaxUint256);
        const dummyProof = ethers.toUtf8Bytes("proof");
        await registry.connect(agentA).register("https://agent-a.meta", 1, dummyProof);

        // 5. Deploy CredentialVerifier (Web of Trust)
        const VerifierFactory = await ethers.getContractFactory("CredentialVerifier");
        verifier = await upgrades.deployProxy(VerifierFactory, [
            admin.address,
            await registry.getAddress(),
            bootstrapVoucher.address,
        ], { kind: "uups" });
        await verifier.waitForDeployment();

        domain = {
            name: "CredentialVerifier",
            version: "1",
            chainId: (await ethers.provider.getNetwork()).chainId as unknown as number,
            verifyingContract: await verifier.getAddress(),
        };
    });

    describe("Bootstrap Vouching", function () {
        it("should accept attestation from bootstrap voucher", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zBootstrapTest"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            const proof = await createAttestation(bootstrapVoucher, agentB.address, didHash, deadline);
            const result = await verifier.verifyCredential.staticCall(agentB.address, proof);
            expect(result).to.be.true;
        });

        it("should record bootstrap voucher in vouchedBy", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zBootstrapRecord"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            const proof = await createAttestation(bootstrapVoucher, agentB.address, didHash, deadline);
            await verifier.verifyCredential(agentB.address, proof);

            expect(await verifier.vouchedBy(agentB.address)).to.equal(bootstrapVoucher.address);
        });
    });

    describe("Registered Agent Vouching", function () {
        it("should accept attestation from a registered agent", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zPeerVouch"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            // agentA is registered → can vouch for agentB
            const proof = await createAttestation(agentA, agentB.address, didHash, deadline);
            const result = await verifier.verifyCredential.staticCall(agentB.address, proof);
            expect(result).to.be.true;
        });

        it("should record voucher in trust path", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zTrustPath"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            const proof = await createAttestation(agentA, agentB.address, didHash, deadline);
            await verifier.verifyCredential(agentB.address, proof);

            expect(await verifier.vouchedBy(agentB.address)).to.equal(agentA.address);
        });
    });

    describe("Trust Path Tracing", function () {
        it("should return correct trust chain via getTrustPath", async function () {
            // Bootstrap vouches for agentA-like scenario (simulate with agentB)
            const didHash1 = ethers.keccak256(ethers.toUtf8Bytes("did:key:zChain1"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            const proof1 = await createAttestation(bootstrapVoucher, agentB.address, didHash1, deadline);
            await verifier.verifyCredential(agentB.address, proof1);

            // Trust path for agentB: [bootstrapVoucher]
            const path = await verifier.getTrustPath(agentB.address, 5);
            expect(path.length).to.equal(1);
            expect(path[0]).to.equal(bootstrapVoucher.address);
        });
    });

    describe("Sybil Resistance (Nullifier)", function () {
        it("should reject second registration with same DID", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zSybilWoT"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            const proof1 = await createAttestation(agentA, agentB.address, didHash, deadline);
            await verifier.verifyCredential(agentB.address, proof1);

            const proof2 = await createAttestation(agentA, attacker.address, didHash, deadline);
            await expect(
                verifier.verifyCredential(attacker.address, proof2)
            ).to.be.revertedWith("Nullifier already used");
        });
    });

    describe("Deadline Enforcement", function () {
        it("should reject expired attestation", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zExpiredWoT"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) - 3600);

            const proof = await createAttestation(agentA, agentB.address, didHash, deadline);
            await expect(
                verifier.verifyCredential(agentB.address, proof)
            ).to.be.revertedWith("Attestation expired");
        });
    });

    describe("Unauthorized Voucher", function () {
        it("should reject attestation from unregistered non-bootstrap address", async function () {
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zUnauthorized"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

            // attacker is neither registered nor bootstrap voucher
            const proof = await createAttestation(attacker, agentB.address, didHash, deadline);
            await expect(
                verifier.verifyCredential(agentB.address, proof)
            ).to.be.revertedWith("Voucher not authorized");
        });
    });

    describe("Admin Functions", function () {
        it("should allow admin to update bootstrap voucher", async function () {
            await verifier.connect(admin).setBootstrapVoucher(attacker.address);
            expect(await verifier.bootstrapVoucher()).to.equal(attacker.address);
        });

        it("should allow admin to disable bootstrap (set to zero)", async function () {
            await verifier.connect(admin).setBootstrapVoucher(ethers.ZeroAddress);
            expect(await verifier.bootstrapVoucher()).to.equal(ethers.ZeroAddress);

            // Now bootstrap attestation should fail
            const didHash = ethers.keccak256(ethers.toUtf8Bytes("did:key:zNoBootstrap"));
            const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);
            const proof = await createAttestation(bootstrapVoucher, agentB.address, didHash, deadline);
            await expect(
                verifier.verifyCredential(agentB.address, proof)
            ).to.be.revertedWith("Voucher not authorized");
        });

        it("should reject non-admin bootstrap voucher update", async function () {
            await expect(
                verifier.connect(attacker).setBootstrapVoucher(attacker.address)
            ).to.be.reverted;
        });
    });
});
