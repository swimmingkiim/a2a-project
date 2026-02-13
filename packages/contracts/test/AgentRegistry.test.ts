import { expect } from "chai";
import { ethers } from "hardhat";
import { AgentRegistry, MockV3Aggregator, MockVerifier, ComputeToken } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("AgentRegistry (Quadratic Staking)", function () {
    let registry: AgentRegistry;
    let compToken: ComputeToken;
    let mockOracle: MockV3Aggregator;
    let mockVerifier: MockVerifier;
    let admin: SignerWithAddress;
    let user: SignerWithAddress;
    let treasury: SignerWithAddress;
    let deployer: SignerWithAddress;
    let paymaster: SignerWithAddress; // Renamed from treasury, also acts as fee recipient
    let agent1: SignerWithAddress; // Renamed from user
    let agent2: SignerWithAddress; // New signer, not used in this snippet but good for consistency

    const BASE_STAKE_USD = ethers.parseUnits("10", 8); // $10 USD (from contract constant)
    // We'll set Oracle Price to $1.00 for easy math
    const ORACLE_PRICE = ethers.parseUnits("1", 8);

    beforeEach(async function () {
        [deployer, paymaster, agent1, agent2] = await ethers.getSigners();

        // 1. Deploy Mock Token
        const TokenFactory = await ethers.getContractFactory("ComputeToken");
        // Pass name, symbol, and paymaster address as the initial Paymaster/Minter role holder for testing simplicity
        compToken = await TokenFactory.deploy("Test Token", "TEST", paymaster.address);
        await compToken.waitForDeployment();

        // Mint tokens to agent1 for staking
        // 100,000 COMP should be enough for any test
        const MINTER_ROLE = await compToken.MINTER_ROLE();
        // Admin already has MINTER_ROLE from deployment if we passed admin address
        // But let's verify or grant if needed. In strict mode, constructor only grants to msg.sender (admin) and passed paymaster.
        // Here passed paymaster is admin. So admin is MINTER.
        await compToken.mint(user.address, ethers.parseEther("100000"));

        // 2. Deploy Mock Oracle
        const OracleFactory = await ethers.getContractFactory("MockV3Aggregator");
        mockOracle = await OracleFactory.deploy(8, ORACLE_PRICE); // 8 decimals, $1.00
        await mockOracle.waitForDeployment();

        // 3. Deploy Mock Verifier
        const VerifierFactory = await ethers.getContractFactory("MockVerifier");
        mockVerifier = await VerifierFactory.deploy();
        await mockVerifier.waitForDeployment();

        // 4. Deploy AgentRegistry
        const RegistryFactory = await ethers.getContractFactory("AgentRegistry");
        registry = await RegistryFactory.deploy(
            await compToken.getAddress(),
            await mockOracle.getAddress(),
            treasury.address,
            await mockVerifier.getAddress(),
            admin.address
        );
        await registry.waitForDeployment();

        // Approve registry to spend user tokens
        await compToken.connect(user).approve(await registry.getAddress(), ethers.MaxUint256);
    });

    describe("Quadratic Cost Calculation", function () {
        it("should calculate correct cost for 1 Unit", async function () {
            // Cost = $10 * (1^2) = $10
            // Oracle = $1.00 -> 10 COMP
            const cost = await registry.getCompAmountFromUSD(ethers.parseUnits("10", 8));

            // Register with 1 Unit
            const dummyProof = ethers.toUtf8Bytes("proof");
            await expect(registry.connect(user).register("meta", 1, dummyProof))
                .to.emit(registry, "AgentRegistered")
                .withArgs(user.address, "meta", 1, cost);
        });

        it("should calculate correct cost for 10 Units (Quadratic)", async function () {
            // Cost = $10 * (10^2) = $1000
            // Linear would be $100 -> Quadratic is 10x more expensive
            // Oracle = $1.00 -> 1000 COMP
            const expectedCostUSD = BigInt(1000) * BigInt(1e8);
            const expectedComp = await registry.getCompAmountFromUSD(expectedCostUSD);

            const dummyProof = ethers.toUtf8Bytes("proof");
            await expect(registry.connect(user).register("meta", 10, dummyProof))
                .to.emit(registry, "AgentRegistered")
                .withArgs(user.address, "meta", 10, expectedComp);
        });

        it("should calculate correct cost for 100 Units (Max)", async function () {
            // Cost = $10 * (100^2) = $100,000
            // Oracle = $1.00 -> 100,000 COMP
            const expectedCostUSD = BigInt(100000) * BigInt(1e8);
            const expectedComp = await registry.getCompAmountFromUSD(expectedCostUSD);

            const dummyProof = ethers.toUtf8Bytes("proof");
            await expect(registry.connect(user).register("meta", 100, dummyProof))
                .to.emit(registry, "AgentRegistered")
                .withArgs(user.address, "meta", 100, expectedComp);
        });
    });

    describe("Sybil Resistance (Mock DID)", function () {
        it("should prevent registration if Verifier fails", async function () {
            await mockVerifier.setShouldPass(false); // Simulate invalid credential
            const dummyProof = ethers.toUtf8Bytes("invalid");

            await expect(
                registry.connect(user).register("meta", 1, dummyProof)
            ).to.be.revertedWith("Invalid Verified Credential");
        });
    });

    describe("Oracle Updates", function () {
        it("should adjust COMP cost when price changes", async function () {
            // Set Price to $2.00
            await mockOracle.updatePrice(ethers.parseUnits("2", 8));

            // Cost for 1 Unit is still $10 USD
            // At $2.00/COMP, that is 5 COMP
            const startBalance = await compToken.balanceOf(user.address);

            const dummyProof = ethers.toUtf8Bytes("proof");
            await registry.connect(user).register("meta", 1, dummyProof);

            const endBalance = await compToken.balanceOf(user.address);
            const paid = startBalance - endBalance;

            const expectedComp = ethers.parseEther("5");
            expect(paid).to.equal(expectedComp);
        });
    });

    describe("Slashing", function () {
        it("should allow admin to slash stake to Treasury", async function () {
            // Standard registration
            const dummyProof = ethers.toUtf8Bytes("proof");
            await registry.connect(user).register("meta", 1, dummyProof);

            const stake = (await registry.agents(user.address)).stakedAmount;

            // Admin Slashes
            await expect(registry.connect(admin).slash(user.address))
                .to.emit(registry, "AgentSlashed")
                .withArgs(user.address, stake, treasury.address);

            // Verify Treasury Received Funds
            expect(await compToken.balanceOf(treasury.address)).to.equal(stake);

            // Verify Agent Removed
            const agent = await registry.agents(user.address);
            expect(agent.isRegistered).to.be.false;
        });
    });
});
