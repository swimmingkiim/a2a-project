import { expect } from "chai";
import { ethers } from "hardhat";
import { ComputeToken } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { loadFixture } from "@nomicfoundation/hardhat-toolbox/network-helpers";

describe("ComputeToken", () => {
    // Fixture for deploying the contract
    async function deployComputeTokenFixture() {
        const [deployer, paymaster, user1, user2, unauthorized] = await ethers.getSigners();

        const ComputeToken = await ethers.getContractFactory("ComputeToken");
        const computeToken = await ComputeToken.deploy("Compute Token", "COMP", paymaster.address);

        return { computeToken, deployer, paymaster, user1, user2, unauthorized };
    }

    describe("Deployment", () => {
        it("should set the correct name and symbol", async () => {
            const { computeToken } = await loadFixture(deployComputeTokenFixture);

            expect(await computeToken.name()).to.equal("Compute Token");
            expect(await computeToken.symbol()).to.equal("COMP");
        });

        it("should set correct decimals (18)", async () => {
            const { computeToken } = await loadFixture(deployComputeTokenFixture);

            expect(await computeToken.decimals()).to.equal(18);
        });

        it("should have zero initial supply", async () => {
            const { computeToken } = await loadFixture(deployComputeTokenFixture);

            expect(await computeToken.totalSupply()).to.equal(0);
        });

        it("should grant DEFAULT_ADMIN_ROLE to deployer", async () => {
            const { computeToken, deployer } = await loadFixture(deployComputeTokenFixture);

            const DEFAULT_ADMIN_ROLE = await computeToken.DEFAULT_ADMIN_ROLE();
            expect(await computeToken.hasRole(DEFAULT_ADMIN_ROLE, deployer.address)).to.be.true;
        });

        it("should grant MINTER_ROLE to paymaster address", async () => {
            const { computeToken, paymaster } = await loadFixture(deployComputeTokenFixture);

            const MINTER_ROLE = await computeToken.MINTER_ROLE();
            expect(await computeToken.hasRole(MINTER_ROLE, paymaster.address)).to.be.true;
        });
    });

    describe("Access Control - Minting", () => {
        it("should revert when non-minter tries to mint", async () => {
            const { computeToken, unauthorized, user1 } = await loadFixture(deployComputeTokenFixture);

            const amount = ethers.parseEther("1000");

            await expect(
                computeToken.connect(unauthorized).mint(user1.address, amount)
            ).to.be.revertedWithCustomError(
                computeToken,
                "AccessControlUnauthorizedAccount"
            );
        });

        it("should allow MINTER_ROLE to mint tokens", async () => {
            const { computeToken, paymaster, user1 } = await loadFixture(deployComputeTokenFixture);

            const amount = ethers.parseEther("1000");

            await expect(computeToken.connect(paymaster).mint(user1.address, amount))
                .to.emit(computeToken, "Transfer")
                .withArgs(ethers.ZeroAddress, user1.address, amount);

            expect(await computeToken.balanceOf(user1.address)).to.equal(amount);
            expect(await computeToken.totalSupply()).to.equal(amount);
        });

        it("should allow admin to grant MINTER_ROLE to new address", async () => {
            const { computeToken, deployer, user2 } = await loadFixture(deployComputeTokenFixture);

            const MINTER_ROLE = await computeToken.MINTER_ROLE();

            // Grant role
            await computeToken.connect(deployer).grantRole(MINTER_ROLE, user2.address);

            expect(await computeToken.hasRole(MINTER_ROLE, user2.address)).to.be.true;

            // Verify new minter can mint
            const amount = ethers.parseEther("500");
            await expect(computeToken.connect(user2).mint(user2.address, amount))
                .to.emit(computeToken, "Transfer");
        });

        it("should allow admin to revoke MINTER_ROLE", async () => {
            const { computeToken, deployer, paymaster, user1 } = await loadFixture(deployComputeTokenFixture);

            const MINTER_ROLE = await computeToken.MINTER_ROLE();

            // Revoke role
            await computeToken.connect(deployer).revokeRole(MINTER_ROLE, paymaster.address);

            expect(await computeToken.hasRole(MINTER_ROLE, paymaster.address)).to.be.false;

            // Verify revoked minter cannot mint
            await expect(
                computeToken.connect(paymaster).mint(user1.address, ethers.parseEther("100"))
            ).to.be.revertedWithCustomError(computeToken, "AccessControlUnauthorizedAccount");
        });
    });

    describe("Burning Mechanics - Deflationary Proof", () => {
        it("should reduce totalSupply when tokens are burned", async () => {
            const { computeToken, paymaster, user1 } = await loadFixture(deployComputeTokenFixture);

            // Mint 1000 tokens
            const mintAmount = ethers.parseEther("1000");
            await computeToken.connect(paymaster).mint(user1.address, mintAmount);

            const initialSupply = await computeToken.totalSupply();
            expect(initialSupply).to.equal(mintAmount);

            // Burn 300 tokens
            const burnAmount = ethers.parseEther("300");
            await computeToken.connect(user1).burn(burnAmount);

            // Verify supply decreased
            const finalSupply = await computeToken.totalSupply();
            expect(finalSupply).to.equal(mintAmount - burnAmount);
            expect(finalSupply).to.equal(ethers.parseEther("700"));
        });

        it("should allow any holder to burn their own tokens", async () => {
            const { computeToken, paymaster, user1 } = await loadFixture(deployComputeTokenFixture);

            // Mint 500 tokens to user
            const mintAmount = ethers.parseEther("500");
            await computeToken.connect(paymaster).mint(user1.address, mintAmount);

            // User burns 100 tokens
            const burnAmount = ethers.parseEther("100");
            await expect(computeToken.connect(user1).burn(burnAmount))
                .to.emit(computeToken, "Transfer")
                .withArgs(user1.address, ethers.ZeroAddress, burnAmount);

            // Verify balance reduced
            expect(await computeToken.balanceOf(user1.address)).to.equal(ethers.parseEther("400"));
        });

        it("should revert when burning more than balance", async () => {
            const { computeToken, paymaster, user1 } = await loadFixture(deployComputeTokenFixture);

            // Mint 100 tokens
            await computeToken.connect(paymaster).mint(user1.address, ethers.parseEther("100"));

            // Try to burn 200 tokens (more than balance)
            await expect(
                computeToken.connect(user1).burn(ethers.parseEther("200"))
            ).to.be.revertedWithCustomError(computeToken, "ERC20InsufficientBalance");
        });

        it("should emit Transfer event to zero address when burning", async () => {
            const { computeToken, paymaster, user1 } = await loadFixture(deployComputeTokenFixture);

            await computeToken.connect(paymaster).mint(user1.address, ethers.parseEther("1000"));

            const burnAmount = ethers.parseEther("250");
            await expect(computeToken.connect(user1).burn(burnAmount))
                .to.emit(computeToken, "Transfer")
                .withArgs(user1.address, ethers.ZeroAddress, burnAmount);
        });
    });

    describe("ERC20 Standard Compliance", () => {
        it("should transfer tokens between accounts", async () => {
            const { computeToken, paymaster, user1, user2 } = await loadFixture(deployComputeTokenFixture);

            // Mint to user1
            await computeToken.connect(paymaster).mint(user1.address, ethers.parseEther("1000"));

            // Transfer to user2
            const transferAmount = ethers.parseEther("400");
            await expect(computeToken.connect(user1).transfer(user2.address, transferAmount))
                .to.emit(computeToken, "Transfer")
                .withArgs(user1.address, user2.address, transferAmount);

            expect(await computeToken.balanceOf(user1.address)).to.equal(ethers.parseEther("600"));
            expect(await computeToken.balanceOf(user2.address)).to.equal(transferAmount);
        });

        it("should approve and transferFrom correctly", async () => {
            const { computeToken, paymaster, user1, user2 } = await loadFixture(deployComputeTokenFixture);

            // Mint to user1
            await computeToken.connect(paymaster).mint(user1.address, ethers.parseEther("1000"));

            // Approve user2 to spend
            const approvalAmount = ethers.parseEther("500");
            await computeToken.connect(user1).approve(user2.address, approvalAmount);

            expect(await computeToken.allowance(user1.address, user2.address)).to.equal(approvalAmount);

            // User2 transfers from user1
            const transferAmount = ethers.parseEther("300");
            await expect(
                computeToken.connect(user2).transferFrom(user1.address, user2.address, transferAmount)
            ).to.emit(computeToken, "Transfer");

            expect(await computeToken.balanceOf(user2.address)).to.equal(transferAmount);
            expect(await computeToken.allowance(user1.address, user2.address)).to.equal(
                approvalAmount - transferAmount
            );
        });
    });

    describe("BME Economic Model Simulation", () => {
        it("should support mint-then-burn cycle (deflationary scenario)", async () => {
            const { computeToken, paymaster, user1 } = await loadFixture(deployComputeTokenFixture);

            // Simulate network growth: Mint rewards
            await computeToken.connect(paymaster).mint(user1.address, ethers.parseEther("10000"));
            expect(await computeToken.totalSupply()).to.equal(ethers.parseEther("10000"));

            // Simulate high usage: Burn fees (more than minted)
            await computeToken.connect(user1).burn(ethers.parseEther("6000"));

            // Net result: Deflationary (supply decreased)
            expect(await computeToken.totalSupply()).to.equal(ethers.parseEther("4000"));
        });

        it("should demonstrate inflationary scenario (mint > burn)", async () => {
            const { computeToken, paymaster, user1, user2 } = await loadFixture(deployComputeTokenFixture);

            // Mint 5000 to user1
            await computeToken.connect(paymaster).mint(user1.address, ethers.parseEther("5000"));

            // Mint 3000 to user2
            await computeToken.connect(paymaster).mint(user2.address, ethers.parseEther("3000"));

            // Total minted: 8000
            expect(await computeToken.totalSupply()).to.equal(ethers.parseEther("8000"));

            // Burn only 2000
            await computeToken.connect(user1).burn(ethers.parseEther("2000"));

            // Net result: Inflationary (supply increased from 0 to 6000)
            expect(await computeToken.totalSupply()).to.equal(ethers.parseEther("6000"));
        });
    });
});
