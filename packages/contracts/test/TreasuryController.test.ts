import { expect } from "chai";
import { ethers } from "hardhat";
import { TreasuryController } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { time } from "@nomicfoundation/hardhat-network-helpers";

describe("TreasuryController (PID)", function () {
    let treasuryController: TreasuryController;
    let admin: SignerWithAddress;
    let keeper: SignerWithAddress;
    let user: SignerWithAddress;

    const TARGET_PRICE = ethers.parseEther("50"); // $50 USD
    const EPOCH_DURATION = 3600; // 1 hour

    beforeEach(async function () {
        [admin, keeper, user] = await ethers.getSigners();

        const TreasuryControllerFactory = await ethers.getContractFactory("TreasuryController");
        treasuryController = await TreasuryControllerFactory.deploy(
            admin.address,
            TARGET_PRICE,
            EPOCH_DURATION
        );
        await treasuryController.waitForDeployment();
    });

    describe("Deployment", function () {
        it("should set the correct initial values", async function () {
            const rates = await treasuryController.getRates();
            expect(rates[0]).to.equal(ethers.parseEther("0.5")); // 50% Burn
            expect(rates[1]).to.equal(ethers.parseEther("0.5")); // 50% Recycle
        });

        it("should grant ADMIN_ROLE to deployer", async function () {
            const ADMIN_ROLE = await treasuryController.ADMIN_ROLE();
            expect(await treasuryController.hasRole(ADMIN_ROLE, admin.address)).to.be.true;
        });
    });

    describe("PID Update Logic", function () {
        it("should fail if epoch has not passed", async function () {
            await expect(treasuryController.updateEpoch(ethers.parseEther("50"))).to.be.revertedWithCustomError(
                treasuryController,
                "EpochNotFinished"
            );
        });

        it("should increase Burn Rate when price is UNDER target (Undervalued)", async function () {
            // Undervalued: Price = $40 (Target $50) -> Error = +10 -> Output > 0 -> Burn Rate Increases
            await time.increase(EPOCH_DURATION + 1);

            const currentPrice = ethers.parseEther("40");
            await expect(treasuryController.updateEpoch(currentPrice))
                .to.emit(treasuryController, "RatesUpdated");

            const rates = await treasuryController.getRates();
            expect(rates[0]).to.be.gt(ethers.parseEther("0.5")); // Burn Rate > 50%
            expect(rates[1]).to.be.lt(ethers.parseEther("0.5")); // Recycle Rate < 50%
        });

        it("should decrease Burn Rate when price is OVER target (Overvalued)", async function () {
            // Overvalued: Price = $60 (Target $50) -> Error = -10 -> Output < 0 -> Burn Rate Decreases
            await time.increase(EPOCH_DURATION + 1);

            const currentPrice = ethers.parseEther("60");
            await treasuryController.updateEpoch(currentPrice);

            const rates = await treasuryController.getRates();
            expect(rates[0]).to.be.lt(ethers.parseEther("0.5")); // Burn Rate < 50%
            expect(rates[1]).to.be.gt(ethers.parseEther("0.5")); // Recycle Rate > 50%
        });

        it("should clamp rates within [0.1, 0.9]", async function () {
            // Massive Undervaluation: Price = $1 (Target $50)
            await time.increase(EPOCH_DURATION + 1);
            await treasuryController.updateEpoch(ethers.parseEther("1"));

            let rates = await treasuryController.getRates();
            expect(rates[0]).to.be.lte(ethers.parseEther("0.9")); // Max 90%

            // Massive Overvaluation: Price = $1000 (Target $50)
            await time.increase(EPOCH_DURATION + 1);
            await treasuryController.updateEpoch(ethers.parseEther("1000"));

            rates = await treasuryController.getRates();
            expect(rates[0]).to.be.gte(ethers.parseEther("0.1")); // Min 10%
        });
    });

    describe("Admin Functions", function () {
        it("should allow admin to update coefficients", async function () {
            const newKp = ethers.parseEther("2");
            const newKi = ethers.parseEther("0.5");
            const newKd = ethers.parseEther("1");

            await expect(treasuryController.connect(admin).updateCoefficients(newKp, newKi, newKd))
                .to.emit(treasuryController, "CoefficientsUpdated")
                .withArgs(newKp, newKi, newKd);
        });

        it("should prevent non-admin from updating coefficients", async function () {
            await expect(
                treasuryController.connect(user).updateCoefficients(0, 0, 0)
            ).to.be.reverted; // AccessControl error
        });
    });
});
