import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { DaimToken } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { loadFixture } from "@nomicfoundation/hardhat-toolbox/network-helpers";

describe("DaimToken", () => {
    // Fixture for deploying the contract
    async function deployDaimTokenFixture() {
        const [deployer, paymaster, user1, user2, unauthorized] = await ethers.getSigners();

        const DaimToken = await ethers.getContractFactory("DaimToken");
        // UUPS Deployment: initialize(defaultAdmin)
        const daimToken = (await upgrades.deployProxy(DaimToken, [deployer.address], { kind: 'uups' })) as unknown as DaimToken;
        await daimToken.waitForDeployment();

        // Grant MINTER_ROLE to paymaster for testing purposes
        const MINTER_ROLE = await daimToken.MINTER_ROLE();
        await daimToken.grantRole(MINTER_ROLE, paymaster.address);

        return { daimToken, deployer, paymaster, user1, user2, unauthorized };
    }

    describe("Deployment", () => {
        it("should set the correct name and symbol", async () => {
            const { daimToken } = await loadFixture(deployDaimTokenFixture);

            expect(await daimToken.name()).to.equal("Eudaimon");
            expect(await daimToken.symbol()).to.equal("DAIM");
        });

        it("should set correct decimals (18)", async () => {
            const { daimToken } = await loadFixture(deployDaimTokenFixture);

            expect(await daimToken.decimals()).to.equal(18);
        });

        it("should have correct initial supply", async () => {
            const { daimToken } = await loadFixture(deployDaimTokenFixture);

            // 50 Million * 10^18
            const expectedSupply = ethers.parseEther("50000000");
            expect(await daimToken.totalSupply()).to.equal(expectedSupply);
        });

        it("should grant DEFAULT_ADMIN_ROLE to deployer", async () => {
            const { daimToken, deployer } = await loadFixture(deployDaimTokenFixture);

            const DEFAULT_ADMIN_ROLE = await daimToken.DEFAULT_ADMIN_ROLE();
            expect(await daimToken.hasRole(DEFAULT_ADMIN_ROLE, deployer.address)).to.be.true;
        });

        it("should grant MINTER_ROLE to paymaster address", async () => {
            const { daimToken, paymaster } = await loadFixture(deployDaimTokenFixture);

            const MINTER_ROLE = await daimToken.MINTER_ROLE();
            expect(await daimToken.hasRole(MINTER_ROLE, paymaster.address)).to.be.true;
        });
    });

    describe("Access Control - Minting", () => {
        it("should revert when non-minter tries to mint", async () => {
            const { daimToken, unauthorized, user1 } = await loadFixture(deployDaimTokenFixture);

            const amount = ethers.parseEther("1000");

            await expect(
                daimToken.connect(unauthorized).mint(user1.address, amount)
            ).to.be.revertedWithCustomError(
                daimToken,
                "AccessControlUnauthorizedAccount"
            );
        });

        it("should allow MINTER_ROLE to mint tokens", async () => {
            const { daimToken, paymaster, user1 } = await loadFixture(deployDaimTokenFixture);

            const amount = ethers.parseEther("1000");

            await expect(daimToken.connect(paymaster).mint(user1.address, amount))
                .to.emit(daimToken, "Transfer")
                .withArgs(ethers.ZeroAddress, user1.address, amount);

            expect(await daimToken.balanceOf(user1.address)).to.equal(amount);
            // Total Supply = Initial (50M) + Minted (1000)
            const initialSupply = ethers.parseEther("50000000");
            expect(await daimToken.totalSupply()).to.equal(initialSupply + amount);
        });

        it("should allow admin to grant MINTER_ROLE to new address", async () => {
            const { daimToken, deployer, user2 } = await loadFixture(deployDaimTokenFixture);

            const MINTER_ROLE = await daimToken.MINTER_ROLE();

            // Grant role
            await daimToken.connect(deployer).grantRole(MINTER_ROLE, user2.address);

            expect(await daimToken.hasRole(MINTER_ROLE, user2.address)).to.be.true;

            // Verify new minter can mint
            const amount = ethers.parseEther("500");
            await expect(daimToken.connect(user2).mint(user2.address, amount))
                .to.emit(daimToken, "Transfer");
        });

        it("should allow admin to revoke MINTER_ROLE", async () => {
            const { daimToken, deployer, paymaster, user1 } = await loadFixture(deployDaimTokenFixture);

            const MINTER_ROLE = await daimToken.MINTER_ROLE();

            // Revoke role
            await daimToken.connect(deployer).revokeRole(MINTER_ROLE, paymaster.address);

            expect(await daimToken.hasRole(MINTER_ROLE, paymaster.address)).to.be.false;

            // Verify revoked minter cannot mint
            await expect(
                daimToken.connect(paymaster).mint(user1.address, ethers.parseEther("100"))
            ).to.be.revertedWithCustomError(daimToken, "AccessControlUnauthorizedAccount");
        });
    });

    describe("Burning Mechanics - Deflationary Proof", () => {
        it("should reduce totalSupply when tokens are burned", async () => {
            const { daimToken, paymaster, user1 } = await loadFixture(deployDaimTokenFixture);

            // Mint 1000 tokens
            const mintAmount = ethers.parseEther("1000");
            await daimToken.connect(paymaster).mint(user1.address, mintAmount);

            const initialTotalSupply = await daimToken.totalSupply();
            const expectedInitialTotal = ethers.parseEther("50000000") + mintAmount;
            expect(initialTotalSupply).to.equal(expectedInitialTotal);

            // Burn 300 tokens
            const burnAmount = ethers.parseEther("300");
            await daimToken.connect(user1).burn(burnAmount);

            // Verify supply decreased
            const finalSupply = await daimToken.totalSupply();
            expect(finalSupply).to.equal(expectedInitialTotal - burnAmount);
        });

        it("should allow any holder to burn their own tokens", async () => {
            const { daimToken, paymaster, user1 } = await loadFixture(deployDaimTokenFixture);

            // Mint 500 tokens to user
            const mintAmount = ethers.parseEther("500");
            await daimToken.connect(paymaster).mint(user1.address, mintAmount);

            // User burns 100 tokens
            const burnAmount = ethers.parseEther("100");
            await expect(daimToken.connect(user1).burn(burnAmount))
                .to.emit(daimToken, "Transfer")
                .withArgs(user1.address, ethers.ZeroAddress, burnAmount);

            // Verify balance reduced
            expect(await daimToken.balanceOf(user1.address)).to.equal(ethers.parseEther("400"));
        });

        it("should revert when burning more than balance", async () => {
            const { daimToken, paymaster, user1 } = await loadFixture(deployDaimTokenFixture);

            // Mint 100 tokens
            await daimToken.connect(paymaster).mint(user1.address, ethers.parseEther("100"));

            // Try to burn 200 tokens (more than balance)
            await expect(
                daimToken.connect(user1).burn(ethers.parseEther("200"))
            ).to.be.revertedWithCustomError(daimToken, "ERC20InsufficientBalance");
        });

        it("should emit Transfer event to zero address when burning", async () => {
            const { daimToken, paymaster, user1 } = await loadFixture(deployDaimTokenFixture);

            await daimToken.connect(paymaster).mint(user1.address, ethers.parseEther("1000"));

            const burnAmount = ethers.parseEther("250");
            await expect(daimToken.connect(user1).burn(burnAmount))
                .to.emit(daimToken, "Transfer")
                .withArgs(user1.address, ethers.ZeroAddress, burnAmount);
        });
    });

    describe("ERC20 Standard Compliance", () => {
        it("should transfer tokens between accounts", async () => {
            const { daimToken, paymaster, user1, user2 } = await loadFixture(deployDaimTokenFixture);

            // Mint to user1
            await daimToken.connect(paymaster).mint(user1.address, ethers.parseEther("1000"));

            // Transfer to user2
            const transferAmount = ethers.parseEther("400");
            await expect(daimToken.connect(user1).transfer(user2.address, transferAmount))
                .to.emit(daimToken, "Transfer")
                .withArgs(user1.address, user2.address, transferAmount);

            expect(await daimToken.balanceOf(user1.address)).to.equal(ethers.parseEther("600"));
            expect(await daimToken.balanceOf(user2.address)).to.equal(transferAmount);
        });

        it("should approve and transferFrom correctly", async () => {
            const { daimToken, paymaster, user1, user2 } = await loadFixture(deployDaimTokenFixture);

            // Mint to user1
            await daimToken.connect(paymaster).mint(user1.address, ethers.parseEther("1000"));

            // Approve user2 to spend
            const approvalAmount = ethers.parseEther("500");
            await daimToken.connect(user1).approve(user2.address, approvalAmount);

            expect(await daimToken.allowance(user1.address, user2.address)).to.equal(approvalAmount);

            // User2 transfers from user1
            const transferAmount = ethers.parseEther("300");
            await expect(
                daimToken.connect(user2).transferFrom(user1.address, user2.address, transferAmount)
            ).to.emit(daimToken, "Transfer");

            expect(await daimToken.balanceOf(user2.address)).to.equal(transferAmount);
            expect(await daimToken.allowance(user1.address, user2.address)).to.equal(
                approvalAmount - transferAmount
            );
        });
    });

    describe("BME Economic Model Simulation", () => {
        it("should support mint-then-burn cycle (deflationary scenario)", async () => {
            const { daimToken, paymaster, user1 } = await loadFixture(deployDaimTokenFixture);

            const initialSupply = ethers.parseEther("50000000");

            // Simulate network growth: Mint rewards
            const mintAmount = ethers.parseEther("10000");
            await daimToken.connect(paymaster).mint(user1.address, mintAmount);
            expect(await daimToken.totalSupply()).to.equal(initialSupply + mintAmount);

            // Simulate high usage: Burn fees (more than minted)
            const burnAmount = ethers.parseEther("6000");
            await daimToken.connect(user1).burn(burnAmount);

            // Net result: Deflationary (supply decreased)
            expect(await daimToken.totalSupply()).to.equal(initialSupply + mintAmount - burnAmount);
        });

        it("should demonstrate inflationary scenario (mint > burn)", async () => {
            const { daimToken, paymaster, user1, user2 } = await loadFixture(deployDaimTokenFixture);

            const initialSupply = ethers.parseEther("50000000");

            // Mint 5000 to user1
            await daimToken.connect(paymaster).mint(user1.address, ethers.parseEther("5000"));

            // Mint 3000 to user2
            await daimToken.connect(paymaster).mint(user2.address, ethers.parseEther("3000"));

            // Total minted: 8000
            const totalMinted = ethers.parseEther("8000");
            expect(await daimToken.totalSupply()).to.equal(initialSupply + totalMinted);

            // Burn only 2000
            const burnAmount = ethers.parseEther("2000");
            await daimToken.connect(user1).burn(burnAmount);

            // Net result: Inflationary (supply increased from 0 to 6000)
            expect(await daimToken.totalSupply()).to.equal(initialSupply + totalMinted - burnAmount);
        });
    });
});
