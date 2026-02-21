import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import {
    DaimToken,
    AgentRegistry,
    QuantumTaskBuffer,
    OracleRegistry,
    MockV3Aggregator,
    MockVerifier
} from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("QuantumTaskBuffer & OracleRegistry Test", function () {
    let daimToken: DaimToken;
    let agentRegistry: AgentRegistry;
    let taskBuffer: QuantumTaskBuffer;
    let oracleRegistry: OracleRegistry;
    let mockOracle: MockV3Aggregator;
    let mockVerifier: MockVerifier;

    let deployer: SignerWithAddress;
    let admin: SignerWithAddress;
    let agent: SignerWithAddress;
    let oracle: SignerWithAddress;
    let treasury: SignerWithAddress;

    const BASE_DEPOSIT = ethers.parseEther("10"); // 10 DAIM
    const BASE_REWARD = ethers.parseEther("50"); // 50 DAIM

    beforeEach(async function () {
        [deployer, agent, oracle, treasury] = await ethers.getSigners();
        admin = deployer;

        // 1. Deploy Token
        const TokenFactory = await ethers.getContractFactory("DaimToken");
        daimToken = (await upgrades.deployProxy(TokenFactory, [admin.address], { kind: 'uups' })) as unknown as DaimToken;
        await daimToken.waitForDeployment();

        // 2. Deploy Mock Oracle & Verifier
        const OracleFactory = await ethers.getContractFactory("MockV3Aggregator");
        mockOracle = await OracleFactory.deploy(8, ethers.parseUnits("50", 8));
        await mockOracle.waitForDeployment();

        const VerifierFactory = await ethers.getContractFactory("contracts/mocks/MockVerifier.sol:MockVerifier");
        mockVerifier = await VerifierFactory.deploy();
        await mockVerifier.waitForDeployment();

        // 3. Deploy AgentRegistry
        const RegistryFactory = await ethers.getContractFactory("AgentRegistry");
        agentRegistry = (await upgrades.deployProxy(RegistryFactory, [
            await daimToken.getAddress(),
            await mockOracle.getAddress(),
            treasury.address,
            await mockVerifier.getAddress(),
            admin.address
        ], { kind: 'uups' })) as unknown as AgentRegistry;
        await agentRegistry.waitForDeployment();

        // 4. Deploy OracleRegistry
        const OracleRegFactory = await ethers.getContractFactory("OracleRegistry");
        oracleRegistry = (await upgrades.deployProxy(OracleRegFactory, [admin.address], { kind: 'uups' })) as unknown as OracleRegistry;
        await oracleRegistry.waitForDeployment();

        // 5. Deploy QuantumTaskBuffer
        const BufferFactory = await ethers.getContractFactory("QuantumTaskBuffer");
        taskBuffer = (await upgrades.deployProxy(BufferFactory, [
            await daimToken.getAddress(),
            await agentRegistry.getAddress(),
            treasury.address,
            admin.address
        ], { kind: 'uups' })) as unknown as QuantumTaskBuffer;
        await taskBuffer.waitForDeployment();

        // 6. Wiring
        await taskBuffer.setOracleRegistry(await oracleRegistry.getAddress());

        const MINTER_ROLE = await daimToken.MINTER_ROLE();
        await daimToken.grantRole(MINTER_ROLE, await taskBuffer.getAddress());

        const ORACLE_ROLE = await taskBuffer.ORACLE_ROLE();
        await taskBuffer.grantRole(ORACLE_ROLE, oracle.address);

        const AGENT_ORACLE_ROLE = await agentRegistry.ORACLE_ROLE();
        await agentRegistry.grantRole(AGENT_ORACLE_ROLE, await taskBuffer.getAddress());

        const TASK_BUFFER_ROLE = await oracleRegistry.TASK_BUFFER_ROLE();
        await oracleRegistry.grantRole(TASK_BUFFER_ROLE, await taskBuffer.getAddress());

        // 7. Fund Agent
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        await (daimToken as any).mint(agent.address, ethers.parseEther("1000"));
        await daimToken.connect(agent).approve(await taskBuffer.getAddress(), ethers.MaxUint256);

        // Register agent first to avoid AgentRegistry "Agent not registered" revert on observation
        const dummyProof = ethers.toUtf8Bytes("proof");
        await daimToken.connect(agent).approve(await agentRegistry.getAddress(), ethers.MaxUint256);
        await agentRegistry.connect(agent).register("ipfs://meta", 5, dummyProof);
    });

    it("should split fee to oracle (15%) and return remaining (85%) on SUCCESS", async function () {
        const agentStartBal = await daimToken.balanceOf(agent.address);
        const oracleStartBal = await daimToken.balanceOf(oracle.address);

        // Submit Task with Metadata URI
        const metadataUri = "ipfs://QmTest123";
        const complexityHash = 12345;

        await expect(taskBuffer.connect(agent).submitTask(complexityHash, metadataUri))
            .to.emit(taskBuffer, "TaskSubmitted")
            .withArgs(0, agent.address, BASE_DEPOSIT, false, metadataUri);

        expect(await daimToken.balanceOf(agent.address)).to.equal(agentStartBal - BASE_DEPOSIT);

        // Finalize Task (Success: Complexity >= 20)
        await taskBuffer.connect(oracle).finalizeTask(0, 50, 80);

        // Oracle should get 15% of 10 DAIM = 1.5 DAIM
        const expectedOracleFee = (BASE_DEPOSIT * 15n) / 100n;
        const oracleEndBal = await daimToken.balanceOf(oracle.address);
        expect(oracleEndBal - oracleStartBal).to.equal(expectedOracleFee);

        // Agent should get back 85% of 10 DAIM (8.5 DAIM) + Reward (50 DAIM * 1.8 = 90 DAIM)
        const expectedRefund = BASE_DEPOSIT - expectedOracleFee;
        const reward = BASE_REWARD + (BASE_REWARD * 80n) / 100n; // score is 80

        const agentEndBal = await daimToken.balanceOf(agent.address);
        expect(agentEndBal - (agentStartBal - BASE_DEPOSIT)).to.equal(expectedRefund + reward);

        // Check Oracle Reputation
        const oracleData = await oracleRegistry.oracles(oracle.address);
        expect(oracleData.totalEvaluations).to.equal(1n);
        expect(oracleData.validEvaluations).to.equal(1n);
        expect(oracleData.slashedEvaluations).to.equal(0n);
    });

    it("should split fee to oracle (15%) and send remaining (85%) to treasury on SLASH", async function () {
        const treasuryStartBal = await daimToken.balanceOf(treasury.address);
        const oracleStartBal = await daimToken.balanceOf(oracle.address);

        // Submit Task with Metadata URI
        const metadataUri = "ipfs://QmSpam456";
        await taskBuffer.connect(agent).submitTask(12345, metadataUri);

        // Finalize Task (Slash: Complexity < 20)
        await taskBuffer.connect(oracle).finalizeTask(0, 10, 0);

        // Oracle should get 15% of 10 DAIM = 1.5 DAIM
        const expectedOracleFee = (BASE_DEPOSIT * 15n) / 100n;
        const oracleEndBal = await daimToken.balanceOf(oracle.address);
        expect(oracleEndBal - oracleStartBal).to.equal(expectedOracleFee);

        // Treasury should get 85% of 10 DAIM = 8.5 DAIM
        const expectedSlash = BASE_DEPOSIT - expectedOracleFee;
        const treasuryEndBal = await daimToken.balanceOf(treasury.address);
        expect(treasuryEndBal - treasuryStartBal).to.equal(expectedSlash);

        // Check Oracle Reputation
        const oracleData = await oracleRegistry.oracles(oracle.address);
        expect(oracleData.totalEvaluations).to.equal(1n);
        expect(oracleData.validEvaluations).to.equal(1n); // In MVP, evaluating a slash counts as valid work
    });
});
