import { expect } from "chai";
import { ethers } from "hardhat";
import { SessionKeyModule, CircuitBreakerModule } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { time } from "@nomicfoundation/hardhat-network-helpers";

describe("Bulkhead Architecture (ERC-7579 Modules)", function () {
    let sessionModule: SessionKeyModule;
    let circuitBreaker: CircuitBreakerModule;
    let owner: SignerWithAddress;
    let sessionKey: SignerWithAddress;
    let targetContract: SignerWithAddress;

    const ONE_ETH = ethers.parseEther("1");

    beforeEach(async function () {
        [owner, sessionKey, targetContract] = await ethers.getSigners();

        // Deploy Session Key Module
        // Note: We need a mock ReputationSystem. Pass address(0) for now (0 rep).
        const SessionFactory = await ethers.getContractFactory("SessionKeyModule");
        sessionModule = await SessionFactory.deploy(ethers.ZeroAddress);
        await sessionModule.waitForDeployment();

        // Deploy Circuit Breaker Module
        const CircuitFactory = await ethers.getContractFactory("CircuitBreakerModule");
        circuitBreaker = await CircuitFactory.deploy();
        await circuitBreaker.waitForDeployment();
    });

    describe("SessionKeyModule", function () {
        it("should create a session with correct duration (Default 1 hour)", async function () {
            // Create Session
            await sessionModule.connect(owner).createSession(
                sessionKey.address,
                targetContract.address,
                ONE_ETH
            );

            const session = await sessionModule.getSession(owner.address, sessionKey.address);

            // Check validity
            expect(session.validUntil).to.be.gt(session.validAfter);
            expect(Number(session.validUntil) - Number(session.validAfter)).to.equal(3600); // 1 hour
        });
    });

    describe("CircuitBreakerModule", function () {
        it("should allow outflow within limits", async function () {
            // Pre-check with 0.1 ETH (Under Soft Limit)
            await expect(
                circuitBreaker.connect(owner).preCheck(owner.address, ethers.parseEther("0.1"), "0x")
            ).to.not.be.reverted;
        });

        it("should revert if Soft Limit exceeded (Gradual Throttling)", async function () {
            // Soft Limit is 1 ETH. Send 1.1 ETH.
            // We expect custom error SoftLimitExceeded(uint256)
            // Hardhat matcher needs exact error signature or just name
            await expect(
                circuitBreaker.connect(owner).preCheck(owner.address, ethers.parseEther("1.1"), "0x")
            ).to.be.revertedWithCustomError(circuitBreaker, "SoftLimitExceeded");
        });
    });
});
