import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { AgentRegistry, MockV3Aggregator, MockVerifier, DaimToken } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("AgentRegistry (Quadratic Staking)", function () {
    let registry: AgentRegistry;
    let daimToken: DaimToken;
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
    const ORACLE_PRICE = ethers.parseUnits("1", 8);

    beforeEach(async function () {
        [deployer, paymaster, agent1, agent2] = await ethers.getSigners();
        admin = deployer; // Assign admin to deployer
        user = agent1; // Alias user to agent1
        treasury = paymaster; // Alias treasury to paymaster (or separate if needed)

        // 1. Deploy Mock Token
        const TokenFactory = await ethers.getContractFactory("DaimToken");
        // UUPS Deployment: initialize(defaultAdmin)
        daimToken = (await upgrades.deployProxy(TokenFactory, [deployer.address], { kind: 'uups' })) as unknown as DaimToken;
        await daimToken.waitForDeployment();

        // Grant MINTER_ROLE to paymaster/admin for testing purposes
        const MINTER_ROLE = await daimToken.MINTER_ROLE();
        await daimToken.grantRole(MINTER_ROLE, admin.address);

        // Mint tokens to user for staking
        await daimToken.mint(user.address, ethers.parseEther("100000"));

        // 2. Deploy Mock Oracle
        const OracleFactory = await ethers.getContractFactory("MockV3Aggregator");
        mockOracle = await OracleFactory.deploy(8, ORACLE_PRICE); // 8 decimals, $1.00
        await mockOracle.waitForDeployment();

        // 3. Deploy Mock Verifier
        const VerifierFactory = await ethers.getContractFactory("contracts/mocks/MockVerifier.sol:MockVerifier");
        mockVerifier = await VerifierFactory.deploy();
        await mockVerifier.waitForDeployment();

        // 4. Deploy AgentRegistry
        const RegistryFactory = await ethers.getContractFactory("AgentRegistry");
        // initialize(daimToken, priceFeed, treasury, verifier, admin)
        registry = (await upgrades.deployProxy(RegistryFactory, [
            await daimToken.getAddress(),
            await mockOracle.getAddress(),
            treasury.address, // Treasury Wallet
            await mockVerifier.getAddress(),
            admin.address // Council/Admin
        ], { kind: 'uups' })) as unknown as AgentRegistry;
        await registry.waitForDeployment();

        // Approve registry to spend user tokens
        await daimToken.connect(user).approve(await registry.getAddress(), ethers.MaxUint256);
    });

    describe("Quadratic Cost Calculation", function () {
        it("should calculate correct cost for 1 Unit", async function () {
            // Cost = $10 * (1^2) = $10
            // Oracle = $1.00 -> 10 DAIM
            const cost = await registry.getDaimAmountFromUSD(ethers.parseUnits("10", 8));

            // Register with 1 Unit
            const dummyProof = ethers.toUtf8Bytes("proof");
            await expect(registry.connect(user).register("meta", 1, dummyProof))
                .to.emit(registry, "AgentRegistered")
                .withArgs(user.address, "meta", 1, cost);
        });

        it("should calculate correct cost for 10 Units (Quadratic)", async function () {
            // Cost = $10 * (10^2) = $1000
            // Linear would be $100 -> Quadratic is 10x more expensive
            // Oracle = $1.00 -> 1000 DAIM
            const expectedCostUSD = BigInt(1000) * BigInt(1e8);
            const expectedComp = await registry.getDaimAmountFromUSD(expectedCostUSD);

            const dummyProof = ethers.toUtf8Bytes("proof");
            await expect(registry.connect(user).register("meta", 10, dummyProof))
                .to.emit(registry, "AgentRegistered")
                .withArgs(user.address, "meta", 10, expectedComp);
        });

        it("should calculate correct cost for 100 Units (Max)", async function () {
            // Cost = $10 * (100^2) = $100,000
            // Oracle = $1.00 -> 100,000 DAIM
            const expectedCostUSD = BigInt(100000) * BigInt(1e8);
            const expectedComp = await registry.getDaimAmountFromUSD(expectedCostUSD);

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
        it("should adjust DAIM cost when price changes", async function () {
            // Set Price to $2.00
            await mockOracle.updatePrice(ethers.parseUnits("2", 8));

            // Cost for 1 Unit is still $10 USD
            // At $2.00/DAIM, that is 5 DAIM
            const startBalance = await daimToken.balanceOf(user.address);

            const dummyProof = ethers.toUtf8Bytes("proof");
            await registry.connect(user).register("meta", 1, dummyProof);

            const endBalance = await daimToken.balanceOf(user.address);
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
            expect(await daimToken.balanceOf(treasury.address)).to.equal(stake);

            // Verify Agent Removed
            const agent = await registry.agents(user.address);
            expect(agent.isRegistered).to.be.false;
        });
    });
});
