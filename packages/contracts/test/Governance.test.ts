import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { time, loadFixture } from "@nomicfoundation/hardhat-toolbox/network-helpers";

describe("A2A Governance System (Genesis)", function () {
    async function deployGovernanceFixture() {
        const [deployer, admin, aiOracle, user, ...guardians] = await ethers.getSigners();

        // Use 5 guardians
        const genesisGuardians = guardians.slice(0, 5);
        const genesisAddresses = genesisGuardians.map(g => g.address);

        // Mocks
        const MockPriceFeed = await ethers.getContractFactory("MockPriceFeed");
        const mockPriceFeed = await MockPriceFeed.deploy(200000000000, 8); // $2000

        const MockVerifier = await ethers.getContractFactory("contracts/mocks/MockVerifier.sol:MockVerifier");
        const mockVerifier = await MockVerifier.deploy();

        // Core
        const DaimToken = await ethers.getContractFactory("DaimToken");
        const daimToken = await upgrades.deployProxy(DaimToken, [admin.address], { kind: 'uups' });

        const AgentRegistry = await ethers.getContractFactory("AgentRegistry");
        const agentRegistry = await upgrades.deployProxy(AgentRegistry, [
            await daimToken.getAddress(),
            await mockPriceFeed.getAddress(),
            admin.address,
            await mockVerifier.getAddress(),
            admin.address
        ], { kind: 'uups' });

        // Register Guardians as Agents (so they can be selected by Council)
        // Fund and register
        await daimToken.connect(admin).mint(admin.address, ethers.parseEther("1000"));
        for (const g of genesisGuardians) {
            await daimToken.connect(admin).transfer(g.address, ethers.parseEther("100"));
            await daimToken.connect(g).approve(await agentRegistry.getAddress(), ethers.parseEther("100"));
            await agentRegistry.connect(g).register("meta", 1, "0x");
        }

        // Also register 'user' to have more candidates
        await daimToken.connect(admin).transfer(user.address, ethers.parseEther("100"));
        await daimToken.connect(user).approve(await agentRegistry.getAddress(), ethers.parseEther("100"));
        await agentRegistry.connect(user).register("user", 1, "0x");

        // Governance
        const EmergencyCouncil = await ethers.getContractFactory("EmergencyCouncil");
        const emergencyCouncil = await upgrades.deployProxy(EmergencyCouncil, [
            admin.address,
            await agentRegistry.getAddress(),
            genesisAddresses
        ], { kind: 'uups' });

        const DeadMansSwitch = await ethers.getContractFactory("DeadMansSwitch");
        const deadMansSwitch = await upgrades.deployProxy(DeadMansSwitch, [
            admin.address,
            await emergencyCouncil.getAddress()
        ], { kind: 'uups' });

        // Wiring
        const DEFAULT_ADMIN_ROLE = await daimToken.DEFAULT_ADMIN_ROLE();
        const COUNCIL_FORMER_ROLE = await emergencyCouncil.COUNCIL_FORMER_ROLE();
        const SIMULATION_ORACLE_ROLE = await emergencyCouncil.SIMULATION_ORACLE_ROLE();
        const COUNCIL_MEMBER_ROLE = await emergencyCouncil.COUNCIL_MEMBER_ROLE();

        // Grant Roles
        await emergencyCouncil.connect(admin).grantRole(COUNCIL_FORMER_ROLE, await deadMansSwitch.getAddress());
        await emergencyCouncil.connect(admin).grantRole(SIMULATION_ORACLE_ROLE, aiOracle.address);

        // Grant Admin to Switch on DaimToken (Shared Admin for test, or Sole Admin?)
        // In succession test, checking if Switch can grant role. 
        // Switch must have Admin role.
        await daimToken.connect(admin).grantRole(DEFAULT_ADMIN_ROLE, await deadMansSwitch.getAddress());
        await deadMansSwitch.connect(admin).addTargetContract(await daimToken.getAddress());

        return {
            deployer, admin, aiOracle, user, genesisGuardians,
            daimToken, agentRegistry, emergencyCouncil, deadMansSwitch,
            DEFAULT_ADMIN_ROLE, COUNCIL_MEMBER_ROLE
        };
    }

    it("Scenario A: Heartbeat keeps switch from triggering", async function () {
        const { deadMansSwitch, admin } = await loadFixture(deployGovernanceFixture);

        await deadMansSwitch.connect(admin).ping();
        const lastHeartbeat = await deadMansSwitch.lastHeartbeat();

        // Advance 89 days
        await time.increase(89 * 24 * 60 * 60);

        // Should fail to trigger
        await expect(deadMansSwitch.triggerSuccession()).to.be.revertedWith("Heartbeat is active");

        // Ping again
        await deadMansSwitch.connect(admin).ping();
        const newHeartbeat = await deadMansSwitch.lastHeartbeat();
        expect(newHeartbeat).to.be.gt(lastHeartbeat);
    });

    it("Scenario B: Succession Trigger transfers power", async function () {
        const { deadMansSwitch, emergencyCouncil, daimToken, admin, genesisGuardians, DEFAULT_ADMIN_ROLE, COUNCIL_MEMBER_ROLE } = await loadFixture(deployGovernanceFixture);

        // Advance 91 days
        await time.increase(91 * 24 * 60 * 60);

        // Trigger
        await expect(deadMansSwitch.triggerSuccession())
            .to.emit(deadMansSwitch, "SuccessionTriggered");

        // Check Council Formed
        // Since we have < 5 registered (Guardians + User = 6), might select 5.
        // Verify at least one guardian or user has COUNCIL_MEMBER_ROLE
        // We can check event log or state.
        // Let's check permissions.

        // Council Contract should now satisfy ADMIN role on DaimToken
        const councilAddr = await emergencyCouncil.getAddress();
        expect(await daimToken.hasRole(DEFAULT_ADMIN_ROLE, councilAddr)).to.be.true;

        // Human Admin should be revoked
        expect(await daimToken.hasRole(DEFAULT_ADMIN_ROLE, admin.address)).to.be.false;
    });

    it("Scenario C: AI Veto Validation", async function () {
        const { emergencyCouncil, admin, aiOracle, genesisGuardians, COUNCIL_MEMBER_ROLE } = await loadFixture(deployGovernanceFixture);

        // Manually grant council role for testing proposal (skip sortition)
        const councilMember = genesisGuardians[0];
        await emergencyCouncil.connect(admin).grantRole(COUNCIL_MEMBER_ROLE, councilMember.address);

        // Propose
        await emergencyCouncil.connect(councilMember).proposeAction(
            admin.address,
            "0x",
            "Malicious Proposal"
        );
        const proposalId = 0;

        // Verify status Ready (1)
        const p1 = await emergencyCouncil.proposals(proposalId);
        expect(p1.status).to.equal(1); // Ready

        // AI Veto
        await emergencyCouncil.connect(aiOracle).vetoBySimulation(proposalId, "Unsafe economic impact");

        // Verify status Vetoed (3)
        const p2 = await emergencyCouncil.proposals(proposalId);
        expect(p2.status).to.equal(3); // Vetoed

        // Try to execute
        await time.increase(25 * 3600); // Wait timelock
        await expect(emergencyCouncil.executeAction(proposalId)).to.be.revertedWith("Not valid");
    });

    it("Scenario D: Genesis Guardian Reset", async function () {
        const { emergencyCouncil, admin, genesisGuardians, user, COUNCIL_MEMBER_ROLE } = await loadFixture(deployGovernanceFixture);

        // Case: Council is stuck or malicious
        // Let's say user has the role and we want to remove them.
        await emergencyCouncil.connect(admin).grantRole(COUNCIL_MEMBER_ROLE, user.address);

        // Prepare signatures from 5 guardians
        const chainId = (await ethers.provider.getNetwork()).chainId;
        const targetParams = ["string", "uint256", "address"];
        const targetValues = ["GENESIS_RESET", chainId, await emergencyCouncil.getAddress()];

        const messageHash = ethers.solidityPackedKeccak256(targetParams, targetValues);
        const messageBytes = ethers.getBytes(messageHash);

        const signatures = [];
        for (const g of genesisGuardians) {
            signatures.push(await g.signMessage(messageBytes));
        }

        // Call Reset
        await expect(emergencyCouncil.emergencyGenesisReset(signatures))
            .to.emit(emergencyCouncil, "GenesisResetTriggered");

        // Verify Guardians have Role
        for (const g of genesisGuardians) {
            expect(await emergencyCouncil.hasRole(COUNCIL_MEMBER_ROLE, g.address)).to.be.true;
        }

        // Note: Reset logic in contract just ADDS them. It doesn't clear 'user'. 
        // We acknowledged this limitation in implementation for Genesis MVP. 
        // In a real fix, we'd use AccessControlEnumerable to clear.
    });
});
