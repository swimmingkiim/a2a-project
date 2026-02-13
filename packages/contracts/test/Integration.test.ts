import { expect } from "chai";
import { ethers } from "hardhat";
import {
    ComputeToken,
    TreasuryController,
    AgentRegistry,
    CircuitBreakerModule,
    MockV3Aggregator,
    MockVerifier
} from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { time } from "@nomicfoundation/hardhat-network-helpers";

describe("Full System Integration Test", function () {
    let compToken: ComputeToken;
    let treasuryController: TreasuryController;
    let registry: AgentRegistry;
    let circuitBreaker: CircuitBreakerModule;
    let mockOracle: MockV3Aggregator;
    let mockVerifier: MockVerifier;

    let admin: SignerWithAddress;
    let agent: SignerWithAddress;
    let treasury: SignerWithAddress;

    const TARGET_PRICE = ethers.parseEther("50"); // $50 USD
    const ORACLE_PRICE = ethers.parseUnits("50", 8); // $50 USD (Stable)

    beforeEach(async function () {
        [deployer, agent, treasury] = await ethers.getSigners(); // Updated signer names

        // 1. Deploy Token
        const TokenFactory = await ethers.getContractFactory("ComputeToken");
        compToken = await TokenFactory.deploy("Compute Token", "COMP", deployer.address); // Added name, symbol, and deployer as initial minter
        await compToken.waitForDeployment();

        // Grant minter/paymaster role to deployer (who is also the initial minter)
        // The deployer is already the minter by default from the constructor, so this line is redundant
        // await compToken.grantRole(await compToken.MINTER_ROLE(), deployer.address);
        await compToken.mint(agent.address, ethers.parseEther("10000")); // Seed agent

        // 2. Deploy Oracle
        const OracleFactory = await ethers.getContractFactory("MockV3Aggregator");
        mockOracle = await OracleFactory.deploy(8, ORACLE_PRICE);
        await mockOracle.waitForDeployment();

        // 3. Deploy Treasury Controller (PID)
        const TreasuryFactory = await ethers.getContractFactory("TreasuryController");
        // For this test, Treasury Controller *controls* the policy, but funds live in 'treasury' address
        // In real architecture, Controller might *be* the treasury or manage it. 
        // Here we test logic independent of fund holding for simplicity.
        treasuryController = await TreasuryFactory.deploy(
            admin.address,
            TARGET_PRICE,
            3600 // 1 Hour Epoch
        );
        await treasuryController.waitForDeployment();

        // 4. Deploy Verifier & Registry
        const VerifierFactory = await ethers.getContractFactory("MockVerifier");
        mockVerifier = await VerifierFactory.deploy();
        await mockVerifier.waitForDeployment();

        const RegistryFactory = await ethers.getContractFactory("AgentRegistry");
        registry = await RegistryFactory.deploy(
            await compToken.getAddress(),
            await mockOracle.getAddress(),
            treasury.address,
            await mockVerifier.getAddress(),
            admin.address
        );
        await registry.waitForDeployment();

        // 5. Deploy Circuit Breaker
        const CircuitFactory = await ethers.getContractFactory("CircuitBreakerModule");
        circuitBreaker = await CircuitFactory.deploy();
        await circuitBreaker.waitForDeployment();

        // Approve registry
        await compToken.connect(agent).approve(await registry.getAddress(), ethers.MaxUint256);
    });

    it("should simulate full lifecycle: Registration -> Staking -> PID Adjustment -> Safety Trip", async function () {
        // --- Step 1: Quadratic Staking Registration ---
        console.log("1. Registering Agent with Quadratic Staking...");
        // 5 Units. Cost = $10 * 5^2 = $250.
        // Price is $50/COMP. Required = 5 COMP.
        const startBal = await compToken.balanceOf(agent.address);

        const dummyProof = ethers.toUtf8Bytes("proof");
        await registry.connect(agent).register("ipfs://meta", 5, dummyProof);

        const endBal = await compToken.balanceOf(agent.address);
        const paid = startBal - endBal;

        expect(paid).to.equal(ethers.parseEther("5"));
        console.log("   -> Paid 5 COMP for 5 Units (Correct)");

        // --- Step 2: PID Controller Response to Price Shock ---
        console.log("2. Simulating Price Dump & PID Response...");
        // Price dumps to $25 (Undervalued vs $50 Target).
        await mockOracle.updatePrice(ethers.parseUnits("25", 8));

        // Fast forward 1 hour to allow PID update
        await time.increase(3601);

        // Trigger Epoch Update (mocking a Keeper)
        // Note: In real life, we read price from Oracle inside updateEpoch if linked, 
        // or pass it in. Our TreasuryController takes input for flexibility.
        await treasuryController.updateEpoch(ethers.parseEther("25"));

        const [burnRate, recycleRate] = await treasuryController.getRates();
        console.log(`   -> New Rates: Burn ${ethers.formatEther(burnRate)}, Recycle ${ethers.formatEther(recycleRate)}`);

        // Expect Burn Rate to INCREASE (to deflate supply) because Price ($25) < Target ($50)
        expect(burnRate).to.be.gt(ethers.parseEther("0.5"));
        console.log("   -> Burn Rate Increased (Correct PID Response)");

        // --- Step 3: Circuit Breaker Trigger ---
        console.log("3. Testing Circuit Breaker Safety...");
        // Agent tries to spend 6 ETH equivalent (Mock check)
        // Hard Limit is 5 ETH.

        await expect(
            circuitBreaker.connect(agent).preCheck(agent.address, ethers.parseEther("6"), "0x")
        ).to.be.revertedWithCustomError(circuitBreaker, "HardLimitExceeded");
        console.log("   -> Hard Limit Breached & Blocked (Correct Safety)");
    });
});
